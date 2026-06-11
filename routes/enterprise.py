from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.database import get_db
from app.auth import get_current_user, get_admin_user, get_technician_user
from models.user import User
from models.enterprise import Enterprise, Review
from schemas.enterprise import (
    EnterpriseResponse, EnterpriseCreate, EnterpriseUpdate, EnterpriseUpgradeMomo,
    ReviewCreate, ReviewResponse
)

router = APIRouter(prefix="/enterprises", tags=["Enterprises"])


@router.get("/", response_model=List[EnterpriseResponse])
def get_all_enterprises(db: Session = Depends(get_db)):
    """
    Public route: Returns all registered enterprises.
    Used by catalog browsers and staff to load supermarket names and brand colors.
    """
    return db.query(Enterprise).all()

@router.get("/{enterprise_id}", response_model=EnterpriseResponse)
def get_enterprise(enterprise_id: int, db: Session = Depends(get_db)):
    """
    Public route: Returns details for a single enterprise.
    """
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found")
    return ent

@router.post("/", response_model=EnterpriseResponse, status_code=status.HTTP_201_CREATED)
def create_enterprise(
    ent_data: EnterpriseCreate,
    db: Session = Depends(get_db),
    tech: User = Depends(get_technician_user)
):
    """
    Technician Only: Registers a new enterprise (capped at 3).
    """
    total_enterprises = db.query(Enterprise).count()
    if total_enterprises >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enterprise Limit Reached: The software is restricted to a maximum of 3 enterprises."
        )
        
    new_ent = Enterprise(**ent_data.model_dump())
    db.add(new_ent)
    db.commit()
    db.refresh(new_ent)
    return new_ent

@router.put("/{enterprise_id}", response_model=EnterpriseResponse)
def update_enterprise(
    enterprise_id: int,
    updates: EnterpriseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Proprietor/Technician: Update branding colors, logo, and name.
    Proprietors can only update their own enterprise.
    """
    # Enforce scoping: proprietors cannot edit other enterprises
    if admin.role != "technician" and admin.enterprise_id != enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You can only manage your own enterprise's branding."
        )
        
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found")
        
    update_data = updates.model_dump(exclude_unset=True)
    
    # Restrict is_premium update to technicians only
    if "is_premium" in update_data and admin.role != "technician":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only system technicians can adjust premium subscriptions."
        )
        
    # Restrict branding customization based on subscription tier
    color_fields = ["primary_theme_color", "secondary_theme_color", "accent_theme_color"]
    is_changing_colors = any(field in update_data for field in color_fields)
    
    if is_changing_colors and admin.role != "technician":
        tier = ent.subscription_tier or "free"
        if tier == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Branding theme customization is a premium feature. Please upgrade to Pro or Ultra."
            )
        elif tier == "pro":
            # Check if they already customized theme once
            if ent.theme_changes_count >= 1:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Pro subscription is limited to exactly 1 theme customization edit. Upgrade to Ultra for unlimited edits."
                )
            # Increment theme changes count
            ent.theme_changes_count += 1

    for key, value in update_data.items():
        setattr(ent, key, value)
        
    db.commit()
    db.refresh(ent)
    return ent

@router.post("/{enterprise_id}/upgrade", response_model=EnterpriseResponse)
def upgrade_enterprise(
    enterprise_id: int,
    upgrade_data: EnterpriseUpgradeMomo,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Proprietor/Technician: Upgrades an enterprise to Pro or Ultra subscription using Mobile Money.
    """
    if admin.role != "technician" and admin.enterprise_id != enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You can only upgrade your own enterprise."
        )
        
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found")
        
    target_tier = upgrade_data.tier.lower()
    if target_tier not in ["pro", "ultra"]:
        raise HTTPException(status_code=400, detail="Invalid subscription tier. Choose 'pro' or 'ultra'.")
        
    ent.subscription_tier = target_tier
    ent.is_premium = True
    ent.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
    
    db.commit()
    db.refresh(ent)
    return ent


@router.post("/{enterprise_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_enterprise_review(
    enterprise_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):
    """
    Public route: Creates a customer review for the given enterprise.
    """
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found")
        
    db_review = Review(
        enterprise_id=enterprise_id,
        customer_name=review_data.customer_name,
        rating=review_data.rating,
        comment=review_data.comment
    )
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review


@router.get("/{enterprise_id}/reviews", response_model=List[ReviewResponse])
def get_public_reviews(enterprise_id: int, db: Session = Depends(get_db)):
    """
    Public route: Returns public testimonials (rating >= 4) for the testimonials carousel.
    """
    return db.query(Review).filter(
        Review.enterprise_id == enterprise_id,
        Review.rating >= 4
    ).order_by(Review.created_at.desc()).all()


@router.get("/{enterprise_id}/reviews/all", response_model=List[ReviewResponse])
def get_all_reviews(
    enterprise_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """
    Private route: Returns all reviews (public and negative) for the owner dashboard.
    """
    if admin.role != "technician" and admin.enterprise_id != enterprise_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: You cannot view reviews for this enterprise."
        )
    return db.query(Review).filter(Review.enterprise_id == enterprise_id).order_by(Review.created_at.desc()).all()


