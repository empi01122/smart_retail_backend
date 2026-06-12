import os
import jwt
import urllib.request
import json
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User

def fetch_clerk_user_email_and_name(clerk_id: str) -> tuple[str | None, str | None]:
    """
    Fetches the user's email address and name directly from Clerk Backend API
    using the configured CLERK_SECRET_KEY.
    """
    clerk_secret = os.getenv("CLERK_SECRET_KEY")
    if not clerk_secret:
        print("[AUTH] ⚠️ CLERK_SECRET_KEY is not set in .env")
        return None, None
    try:
        req = urllib.request.Request(
            f"https://api.clerk.com/v1/users/{clerk_id}",
            headers={
                "Authorization": f"Bearer {clerk_secret}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Find primary email
            email = None
            primary_email_id = data.get("primary_email_address_id")
            email_addresses = data.get("email_addresses", [])
            for email_obj in email_addresses:
                if email_obj.get("id") == primary_email_id:
                    email = email_obj.get("email_address")
                    break
            if not email and email_addresses:
                email = email_addresses[0].get("email_address")
            
            first_name = data.get("first_name") or ""
            last_name = data.get("last_name") or ""
            name = f"{first_name} {last_name}".strip() or "Staff Member"
            return email, name
    except Exception as e:
        print(f"[AUTH] ❌ Error fetching user from Clerk API: {e}")
        return None, None


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
    is_debug = ENABLE_DEV_BYPASS or (os.getenv("DEBUG", "False").lower() in ["true", "1"])

    # STEP 1: Check if Authorization header arrived at all
    if credentials is None:
        print("[AUTH] ❌ No Authorization header received in request")
        if is_debug:
            return get_mock_admin(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: Missing Authorization Header"
        )

    token = credentials.credentials
    print(f"[AUTH] ✅ Token received — length={len(token)}, starts with: {token[:30]}...")

    # STEP 2: Bypass check for dev mode
    if is_debug and (token.lower() in ["bypass", "debug", "true", "false", "admin", "test", "null", "undefined"] or len(token) < 20):
        print("[AUTH] 🔓 Dev bypass token detected — returning mock admin")
        return get_mock_admin(db)

    # STEP 3: Ensure Clerk is configured
    if not clerk_issuer or not jwks_client:
        print("[AUTH] ❌ CLERK_ISSUER is not set in .env!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Missing CLERK_ISSUER"
        )

    # STEP 4: Validate JWT
    try:
        print(f"[AUTH] 🔑 Fetching signing key from Clerk JWKS...")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"[AUTH] 🔑 Signing key found. Decoding token...")
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,  # Clerk uses 'azp' not 'aud'
                "leeway": 3600        # 1-hour clock skew tolerance (prevents local clock sync issues)
            }
        )
        clerk_id: str = payload.get("sub")
        email: str = payload.get("email") or payload.get("primary_email_address")
        name: str = payload.get("name") or payload.get("first_name", "Staff Member")

        # Fallback to Clerk API if email is missing from the JWT payload
        if not email and clerk_id:
            print(f"[AUTH] 🔍 Email missing from JWT payload. Querying Clerk Backend API for clerk_id={clerk_id}...")
            clerk_email, clerk_name = fetch_clerk_user_email_and_name(clerk_id)
            if clerk_email:
                email = clerk_email
                print(f"[AUTH] 🔍 Retried Clerk API — Found email: {email}")
            if clerk_name and (not name or name == "Staff Member"):
                name = clerk_name

        print(f"[AUTH] ✅ Token valid — sub={clerk_id} | email={email} | iss={payload.get('iss')}")

        if clerk_id is None:
            print("[AUTH] ❌ Token has no 'sub' claim!")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token: missing sub claim")

    except HTTPException:
        raise  # Never swallow our own HTTPExceptions

    except jwt.ExpiredSignatureError as e:
        print(f"[AUTH] ❌ Token EXPIRED: {e}")
        if is_debug:
            return get_mock_admin(db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired — please sign in again")

    except jwt.InvalidTokenError as e:
        print(f"[AUTH] ❌ Invalid JWT token: {type(e).__name__}: {e}")
        if is_debug:
            return get_mock_admin(db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")

    except Exception as e:
        print(f"[AUTH] ❌ Unexpected JWT error: {type(e).__name__}: {e}")
        if is_debug:
            return get_mock_admin(db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token verification failed: {type(e).__name__}: {e}")

    # STEP 5: Look up user in our DB
    print(f"[AUTH] 🔍 Looking up user in DB with clerk_id={clerk_id}...")
    user = db.query(User).filter(User.clerk_id == clerk_id).first()

    # Check for hardcoded/env-configured technician email
    technician_email = os.getenv("TECHNICIAN_EMAIL")
    is_tech_email = email and technician_email and email.lower() == technician_email.lower()

    if user is None:
        if is_tech_email:
            # Look up if a technician user already exists by email
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Update/link Clerk ID and ensure role is technician
                user.clerk_id = clerk_id
                user.role = "technician"
                user.enterprise_id = None
                if name and name != "Staff Member":
                    user.name = name
                db.commit()
                db.refresh(user)
                print(f"[AUTH] ✅ Linked technician email {email} to technician user record.")
            else:
                # Create a brand new technician user
                print(f"[AUTH] 🚀 Auto-registering configured technician: {email}")
                user = User(
                    clerk_id=clerk_id,
                    name=name,
                    email=email,
                    role="technician",
                    enterprise_id=None
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"[AUTH] ✅ Configured Technician profile created with ID={user.id}")
        else:
            total_users = db.query(User).count()
            print(f"[AUTH] User not found by clerk_id. Total users in DB: {total_users}")

            if total_users == 0 and not technician_email:
                # First ever login fallback — auto-register as system technician
                print(f"[AUTH] 🚀 First user! Auto-registering {email} as technician...")
                user = User(
                    clerk_id=clerk_id,
                    name=name,
                    email=email or "admin@smartretail.com",
                    role="technician",
                    enterprise_id=None
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"[AUTH] ✅ Technician created with ID={user.id}")
            else:
                # Check if pre-authorized by email
                if email:
                    print(f"[AUTH] 🔍 Checking pre-authorization by email: {email}")
                    user = db.query(User).filter(User.email == email, User.clerk_id.is_(None)).first()
                    if user:
                        user.clerk_id = clerk_id
                        if name and name != "Staff Member":
                            user.name = name
                        db.commit()
                        db.refresh(user)
                        print(f"[AUTH] ✅ Linked Clerk ID to pre-authorized user ID={user.id}")

                if user is None:
                    print(f"[AUTH] ❌ Access denied — {email} is not pre-authorized")
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access Denied: You are not pre-authorized. Contact your administrator."
                    )
    else:
        # If user exists, but their email matches the TECHNICIAN_EMAIL, ensure they have the technician role
        if is_tech_email and user.role != "technician":
            user.role = "technician"
            user.enterprise_id = None
            db.commit()
            db.refresh(user)
            print(f"[AUTH] ✅ Updated existing user {email} to technician role.")

    print(f"[AUTH] ✅ Auth complete — user ID={user.id}, role={user.role}, email={user.email}")
    return user



def get_admin_user(current_user: User = Depends(get_current_user)):
    """
    Checks if the user has administrative/proprietor access.
    Both proprietors and technicians can pass this check.
    """
    if current_user.role not in ["technician", "proprietor", "admin", "owner"]:
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
