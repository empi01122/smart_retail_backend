from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.auth import get_admin_user, get_current_user
from models.user import User
from models.enterprise import Enterprise
from schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Retrieves the currently logged-in user profile details (role, email, name).
    """
    return current_user


@router.post("/staff", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_or_sync_user(
    user: UserCreate, 
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Creates a new user in the database (synced from Clerk).
    Usually called by the frontend or Clerk Webhook right after Clerk creates the user.
    """
    # Check if user with that clerk_id or email already exists
    existing_user = db.query(User).filter(
        ((User.clerk_id == user.clerk_id) & (User.clerk_id.is_not(None))) | 
        (User.email == user.email)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already synced or email already in use.")
        
    # Resolve scoping
    target_ent_id = user.enterprise_id or enterprise_id
    if admin.role != "technician":
        target_ent_id = admin.enterprise_id
    elif target_ent_id is None:
        raise HTTPException(status_code=400, detail="Technician must specify an enterprise_id for staff creation.")

    # Fetch enterprise and enforce staff count limit if adding a cashier/employee
    if user.role == "employee" and admin.role != "technician":
        ent = db.query(Enterprise).filter(Enterprise.id == target_ent_id).first()
        if not ent:
            raise HTTPException(status_code=404, detail="Enterprise not found.")
            
        tier = ent.subscription_tier or "free"
        current_staff_count = db.query(User).filter(User.enterprise_id == target_ent_id, User.role == "employee").count()
        
        if tier == "free" and current_staff_count >= 1:
            raise HTTPException(
                status_code=403,
                detail="Staff limit reached: Free Trial accounts are limited to exactly 1 employee. Please upgrade to Pro or Ultra."
            )
        elif tier == "pro" and current_staff_count >= 2:
            raise HTTPException(
                status_code=403,
                detail="Staff limit reached: Pro accounts are limited to exactly 2 employees. Upgrade to Ultra for unlimited employees."
            )

    db_user = User(
        clerk_id=user.clerk_id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_by_id=admin.id,
        enterprise_id=target_ent_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


@router.get("/staff", response_model=List[UserResponse])
def get_all_staff(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Retrieves all staff members (for the Settings -> Staff Accounts page).
    """
    if admin.role == "technician":
        if enterprise_id is not None:
            return db.query(User).filter(User.enterprise_id == enterprise_id).all()
        return db.query(User).all()
    else:
        # Proprietors only see staff of their own enterprise
        return db.query(User).filter(User.enterprise_id == admin.enterprise_id).all()


@router.delete("/staff/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    user_id: int, 
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Removes an employee account from the local database.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Security: Proprietor can only delete their own staff
    if admin.role != "technician" and user.enterprise_id != admin.enterprise_id:
        raise HTTPException(status_code=403, detail="Access Denied: Staff belongs to another enterprise.")
        
    db.delete(user)
    db.commit()
    return
