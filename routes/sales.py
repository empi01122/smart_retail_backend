from fastapi import APIRouter, Depends, HTTPException, status # APIRouter groups. Depends injects dependencies
from sqlalchemy.orm import Session # type hint for the DB session
from typing import List # for returning a list of sales

from app.database import get_db # function that gives us a DB session
from app.auth import get_current_user, get_technician_user # authentication dependency
from models.user import User # User model
from models.sale import Sale # the Sale database model
from schemas.sale import SaleCreate, SaleOut, DisputeResolve # input and output shapes
from services.business_logic import create_sale_with_stock_update # core logic

from typing import List, Optional
from pydantic import BaseModel

class EscrowRelease(BaseModel):
    pin: str

router = APIRouter(prefix="/sales", tags=["Sales"]) # all routes here start with /sales

@router.get("/", response_model=List[SaleOut]) # Get /sales -> return all sales
def get_all_sales(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
): # db + auth injected automatically
    # Lazy auto-release: complete any escrow transactions older than 2 days (48 hours)
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=60)
    expired_sales = db.query(Sale).filter(
        Sale.payment_status == "paid_escrow",
        Sale.created_at < cutoff
    ).all()
    for s in expired_sales:
        s.payment_status = "completed"
    if expired_sales:
        db.commit()

    if current_user.role == "technician":
        if enterprise_id is not None:
            return db.query(Sale).filter(Sale.enterprise_id == enterprise_id).order_by(Sale.created_at.desc()).all()
        return db.query(Sale).order_by(Sale.created_at.desc()).all()
    else:
        # Proprietors and employees are isolated to their own enterprise
        return db.query(Sale).filter(Sale.enterprise_id == current_user.enterprise_id).order_by(Sale.created_at.desc()).all()

@router.post("/", response_model=SaleOut, status_code=201) # POST /sales -> record a new sale
def record_sale(
    sale_data: SaleCreate, 
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
): # receive sale data + db + auth
    # Enforce enterprise_id: proprietors and employees checkout to their own enterprise
    target_ent_id = sale_data.enterprise_id or enterprise_id
    if current_user.role != "technician":
        target_ent_id = current_user.enterprise_id
    elif target_ent_id is None:
        raise HTTPException(status_code=400, detail="Technicians must provide an enterprise_id to record sales.")
        
    return create_sale_with_stock_update(db, sale_data, target_ent_id) # hand off to business logic

@router.post("/{sale_id}/release", response_model=SaleOut)
def release_escrow(
    sale_id: int,
    payload: EscrowRelease,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unlocks escrowed funds for a transaction.
    Takes a 4-digit PIN. If it matches, changes state to 'completed'.
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    # Check permissions: proprietor must belong to the sale's enterprise
    if current_user.role != "technician" and sale.enterprise_id != current_user.enterprise_id:
        raise HTTPException(status_code=403, detail="Access Denied: Transaction belongs to another enterprise.")
        
    if sale.payment_status != "paid_escrow":
        raise HTTPException(status_code=400, detail="Transaction is not currently locked in escrow.")
        
    # Verify delivery PIN
    if sale.delivery_pin != payload.pin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Verification PIN: The PIN entered does not match the delivery verification code."
        )
        
    # Release funds
    sale.payment_status = "completed"
    # Keep the delivery_pin on the record for audit trail, but unlock status
    db.commit()
    db.refresh(sale)
    return sale

@router.post("/{sale_id}/dispute", response_model=SaleOut)
def dispute_transaction(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    if current_user.role != "technician" and sale.enterprise_id != current_user.enterprise_id:
        raise HTTPException(status_code=403, detail="Access Denied: Transaction belongs to another enterprise.")
        
    if sale.payment_status != "paid_escrow":
        raise HTTPException(status_code=400, detail="Only transactions locked in escrow can be disputed.")
        
    sale.payment_status = "disputed"
    db.commit()
    db.refresh(sale)
    return sale

@router.post("/{sale_id}/resolve-dispute", response_model=SaleOut)
def resolve_dispute(
    sale_id: int,
    payload: DisputeResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_technician_user)
):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    if sale.payment_status != "disputed":
        raise HTTPException(status_code=400, detail="Only disputed transactions can be resolved by a technician.")
        
    if payload.action == "release":
        sale.payment_status = "completed"
    elif payload.action == "refund":
        sale.payment_status = "refunded"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'release' or 'refund'.")
        
    db.commit()
    db.refresh(sale)
    return sale
