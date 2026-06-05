import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User

# --- DEVELOPER BYPASS TOGGLE ---
# Set this to True to bypass auth and run queries as the Mock Technician.
# Set this to False to enforce real Clerk authentication checks.
ENABLE_DEV_BYPASS = True

# FastAPI utility to extract the `Bearer <token>` from the request header (auto_error=False for local debug bypass)
security = HTTPBearer(auto_error=False)

# We only need the base URL of your Clerk instance to fetch the JWKS securely
clerk_issuer = os.getenv("CLERK_ISSUER")
jwks_client = PyJWKClient(f"{clerk_issuer}/.well-known/jwks.json") if clerk_issuer else None

def get_mock_admin(db: Session) -> User:
    """
    Creates or retrieves a mock technician user for local development and testing.
    """
    mock_tech = db.query(User).filter(User.role == "technician").first()
    if not mock_tech:
        mock_tech = db.query(User).filter(User.clerk_id == "mock_local_admin_clerk_id").first()
        if not mock_tech:
            mock_tech = User(
                clerk_id="mock_local_admin_clerk_id",
                name="Local Debug Technician",
                email="admin@smartretail.com",
                role="technician",
                enterprise_id=None
            )
            db.add(mock_tech)
            db.commit()
            db.refresh(mock_tech)
    return mock_tech

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    1. Extracts the Clerk Token from the frontend's request.
    2. Dynamically fetches the active JSON Web Key Set (JWKS) from Clerk.
    3. Finds the user in our local `users` database securely.
    """
    # Enforce file-based bypass first, fallback to environment variable
    is_debug = ENABLE_DEV_BYPASS or (os.getenv("DEBUG", "False") == "True")

    if credentials is None:
        if is_debug:
            # Auto-bypass authentication for local development testing in Swagger
            return get_mock_admin(db)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated: Missing Authorization Header"
            )

    token = credentials.credentials
    
    # If in debug mode and user provided a dummy/test token or clear debug/mock value, auto-bypass!
    if is_debug and (token.lower() in ["bypass", "debug", "true", "false", "admin", "test", "null", "undefined"] or len(token) < 20):
        return get_mock_admin(db)
        
    if not clerk_issuer or not jwks_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Missing CLERK_ISSUER"
        )
        
    try:
        # Dynamically grabs the correct signing key from Clerk, validating the token!
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
        
        # Clerk stores the identifying ID in the "sub" (subject) property
        clerk_id: str = payload.get("sub")
        if clerk_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")
            
        email: str = payload.get("email") or payload.get("primary_email_address") # Standard Clerk JWT claims
        name: str = payload.get("name") or payload.get("first_name", "Staff Member")
            
    except Exception as e:
        if is_debug:
            # Fall back to local mock admin in debug mode if token is invalid or expired
            return get_mock_admin(db)
            
        if isinstance(e, jwt.ExpiredSignatureError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        elif isinstance(e, jwt.InvalidTokenError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to verify token signature")
        
    # Security Check: Does this person exist in our system?
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if user is None:
        # Check if this is the very first user registering (Bootstrapping)
        total_users = db.query(User).count()
        if total_users == 0:
            # Automatically register the first user as the system technician
            user = User(
                clerk_id=clerk_id,
                name=name,
                email=email or "admin@smartretail.com", # Fallback if email is missing in Clerk token
                role="technician",
                enterprise_id=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Check if the user was pre-authorized by an admin using their email
            if email:
                user = db.query(User).filter(User.email == email, User.clerk_id.is_(None)).first()
                if user:
                    # Link their Clerk ID to their pre-authorized profile
                    user.clerk_id = clerk_id
                    # Update name if they have a profile name in Clerk
                    if name and name != "Staff Member":
                        user.name = name
                    db.commit()
                    db.refresh(user)
            
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, 
                    detail="Access Denied: You are not pre-authorized to use this application. Please contact your administrator."
                )
        
    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    """
    Checks if the user has administrative/proprietor access.
    Both proprietors and technicians can pass this check.
    """
    if current_user.role not in ["technician", "proprietor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: Proprietor or Technician privileges required."
        )
    return current_user


def get_technician_user(current_user: User = Depends(get_current_user)):
    """
    Checks if the user is the System Technician.
    Only technicians can pass this check (e.g. for managing all enterprises).
    """
    if current_user.role != "technician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: Technician privileges required."
        )
    return current_user
