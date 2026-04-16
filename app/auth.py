import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User

# FastAPI utility to extract the `Bearer <token>` from the request header
security = HTTPBearer()

# We only need the base URL of your Clerk instance to fetch the JWKS securely
clerk_issuer = os.getenv("CLERK_ISSUER")
jwks_client = PyJWKClient(f"{clerk_issuer}/.well-known/jwks.json") if clerk_issuer else None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    1. Extracts the Clerk Token from the frontend's request.
    2. Dynamically fetches the active JSON Web Key Set (JWKS) from Clerk.
    3. Finds the user in our local `users` database securely.
    """
    token = credentials.credentials
    
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
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
    except Exception as e:
        # Failsafe for PyJWKClient fetching errors
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unable to verify token signature")
        
    # Security Check: Does this person exist in our system?
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: You are not authorized to use this application."
        )
        
    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    """
    After we verify who they are (via `get_current_user`), this checks their Role!
    Only Admins can pass this. Employees will be rejected.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: Admin privileges required."
        )
    return current_user
