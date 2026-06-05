from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.auth import get_current_user, get_admin_user, get_technician_user
from models.user import User
from models.enterprise import Enterprise
from schemas.enterprise import EnterpriseResponse, EnterpriseCreate, EnterpriseUpdate

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
        
    for key, value in update_data.items():
        setattr(ent, key, value)
        
    db.commit()
    db.refresh(ent)
    return ent

@router.post("/{enterprise_id}/upgrade", response_model=EnterpriseResponse)
def upgrade_enterprise(
    enterprise_id: int,
    db: Session = Depends(get_db),
    tech: User = Depends(get_technician_user)
):
    """
    Technician Only: Toggles/Upgrades an enterprise to the Premium subscription tier.
    """
    ent = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found")
        
    ent.is_premium = True
    db.commit()
    db.refresh(ent)
    return ent
