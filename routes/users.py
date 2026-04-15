from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import get_admin_user
from models.user import User
from schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_or_sync_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Creates a new user in the database (synced from Clerk).
    Usually called by the frontend or Clerk Webhook right after Clerk creates the user.
    """
    # Check if user with that clerk_id or email already exists
    existing_user = db.query(User).filter((User.clerk_id == user.clerk_id) | (User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already synced or email already in use.")
        
    db_user = User(
        clerk_id=user.clerk_id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_by_id=user.created_by_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/staff", response_model=List[UserResponse])
def get_all_staff(
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Retrieves all staff members (for the Settings -> Staff Accounts page).
    """
    users = db.query(User).all()
    return users


@router.delete("/staff/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    user_id: int, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Removes an employee account from the local database.
    Note: A full implementation should also instruct Clerk via their Backend API to revoke the user. 
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent deleting the last admin or something similar could be added here
    db.delete(user)
    db.commit()
    
    return
