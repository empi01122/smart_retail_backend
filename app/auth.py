import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from models.user import User

# FastAPI utility to extract the `Bearer <token>` from the request header
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    1. Extracts the Clerk Token from the frontend's request.
    2. Decodes it using our Clerk PEM Public Key.
    3. Finds the user in our local `users` database securely.
    """
    token = credentials.credentials
    clerk_public_key = os.getenv("CLERK_PEM_PUBLIC_KEY")
    
    if not clerk_public_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Missing CLERK_PEM_PUBLIC_KEY"
        )
    
    # Properly format the public key if it's missing the header/footer (common issue)
    if "BEGIN PUBLIC KEY" not in clerk_public_key:
        clerk_public_key = f"-----BEGIN PUBLIC KEY-----\n{clerk_public_key}\n-----END PUBLIC KEY-----"
        
    try:
        # Decode the token! Automatically checks signature and expiration
        payload = jwt.decode(token, clerk_public_key, algorithms=["RS256"])
        
        # Clerk stores the identifying ID in the "sub" (subject) property
        clerk_id: str = payload.get("sub")
        if clerk_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")
        
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
