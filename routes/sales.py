from fastapi import APIRouter, Depends, HTTPException, status # APIRouter groups. Depends injects dependencies
from sqlalchemy.orm import Session # type hint for the DB session
from typing import List # for returning a list of sales

from app.database import get_db # function that gives us a DB session
from app.auth import get_current_user, get_technician_user # authentication dependency
from models.user import User # User model
from models.sale import Sale # the Sale database model
from schemas.sale import SaleCreate, SaleOut, DisputeResolve, PublicDisputeRequest, StoreResponseRequest # input and output shapes
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
            sales = db.query(Sale).filter(Sale.enterprise_id == enterprise_id).order_by(Sale.created_at.desc()).all()
        else:
            sales = db.query(Sale).order_by(Sale.created_at.desc()).all()
    else:
        # Proprietors and employees are isolated to their own enterprise
        sales = db.query(Sale).filter(Sale.enterprise_id == current_user.enterprise_id).order_by(Sale.created_at.desc()).all()

    # Security: employees (cashiers) must NOT receive the delivery PIN in the API response.
    # Only proprietors and technicians are trusted with it for escrow release.
    if current_user.role == "employee":
        for s in sales:
            s.delivery_pin = None  # Masked in-memory — not committed to DB

    return sales

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

@router.post("/online", response_model=SaleOut, status_code=201)
def place_online_order(
    sale_data: SaleCreate,
    db: Session = Depends(get_db),
):
    """
    Public endpoint — no authentication required.
    Called from the customer-facing public catalog after MoMo payment.
    Requires enterprise_id and customer info in the payload.
    """
    if not sale_data.enterprise_id:
        raise HTTPException(status_code=400, detail="enterprise_id is required for online orders.")
    if not sale_data.customer_name or not sale_data.customer_phone or not sale_data.delivery_address:
        raise HTTPException(status_code=400, detail="Customer name, phone, and delivery address are required.")

    # Force source to "online" and payment to mobile_money (escrow)
    sale_data.source = "online"
    sale_data.payment_method = "mobile_money"

    return create_sale_with_stock_update(db, sale_data, sale_data.enterprise_id)

@router.get("/online/pending", response_model=List[SaleOut])
def get_pending_online_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns online orders that are still in 'paid_escrow' status
    (i.e. not yet confirmed/dispatched). Used by the cashier POS notification panel.
    """
    query = db.query(Sale).filter(
        Sale.source == "online",
        Sale.payment_status == "paid_escrow"
    )
    if current_user.role != "technician":
        query = query.filter(Sale.enterprise_id == current_user.enterprise_id)
    return query.order_by(Sale.created_at.desc()).all()


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

@router.post("/{sale_id}/confirm", response_model=SaleOut)
def confirm_online_order(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cashier endpoint: reviews and confirms/dispatches an online order.
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    if current_user.role != "technician" and sale.enterprise_id != current_user.enterprise_id:
        raise HTTPException(status_code=403, detail="Access Denied: Transaction belongs to another enterprise.")
        
    if sale.source != "online":
        raise HTTPException(status_code=400, detail="Only online delivery orders can be confirmed.")
        
    sale.is_confirmed = True
    db.commit()
    db.refresh(sale)
    return sale

@router.post("/{sale_id}/dispute/public", response_model=SaleOut)
def dispute_transaction_public(
    sale_id: int,
    payload: PublicDisputeRequest,
    db: Session = Depends(get_db)
):
    """
    Public customer endpoint: file a dispute directly from the customer receipt view.
    Requires validating client customer_phone and their delivery_pin.
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    if sale.source != "online":
        raise HTTPException(status_code=400, detail="Only online delivery orders can be disputed.")
        
    # Verify customer identity using phone and delivery PIN
    import re
    # Clean up phone prefixes
    clean_client = re.sub(r'[\s\-]', '', payload.customer_phone)
    if clean_client.startswith('+237'): clean_client = clean_client[4:]
    elif clean_client.startswith('237'): clean_client = clean_client[3:]
    
    clean_db = re.sub(r'[\s\-]', '', sale.customer_phone or '')
    if clean_db.startswith('+237'): clean_db = clean_db[4:]
    elif clean_db.startswith('237'): clean_db = clean_db[3:]

    if clean_client != clean_db or sale.delivery_pin != payload.delivery_pin:
        raise HTTPException(
            status_code=400,
            detail="Invalid Verification Details: Phone number or delivery PIN does not match the purchase record."
        )
        
    if sale.payment_status != "paid_escrow":
        raise HTTPException(status_code=400, detail="Only transactions currently locked in escrow can be disputed.")
        
    sale.payment_status = "disputed"
    sale.dispute_reason = payload.dispute_reason
    sale.dispute_picture = payload.dispute_picture
    db.commit()
    db.refresh(sale)
    return sale

@router.get("/public/track", response_model=SaleOut)
def track_order_public(
    receipt_number: str,
    customer_phone: str,
    db: Session = Depends(get_db)
):
    """
    Public customer endpoint: look up order status and retrieve details.
    Requires customer phone verification to ensure security.
    """
    import re
    # Clean client phone
    clean_client = re.sub(r'[\s\-]', '', customer_phone)
    if clean_client.startswith('+237'): clean_client = clean_client[4:]
    elif clean_client.startswith('237'): clean_client = clean_client[3:]
    
    # Parse sale ID from receipt number (PDT[CODE][YEAR][ID])
    # e.g., PDTENTA20260001 -> Extract digits at the end: 20260001.
    # Year is 4 digits (2026), ID is the rest (0001 -> 1).
    sale_id = None
    normalized_rn = receipt_number.strip().upper()
    if normalized_rn.startswith("PDT"):
        match = re.search(r'\d+$', normalized_rn)
        if match:
            suffix = match.group(0)
            if len(suffix) > 4:
                try:
                    sale_id = int(suffix[4:])
                except ValueError:
                    pass
    
    if sale_id is None:
        # Fallback to direct numeric ID parsing if receipt number doesn't fit standard pattern
        try:
            sale_id = int(normalized_rn.replace("#", ""))
        except ValueError:
            pass
            
    if sale_id is None:
        raise HTTPException(status_code=404, detail="Invalid receipt number format.")
        
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Order not found.")
        
    # Check that this is indeed an online order
    if sale.source != "online":
        raise HTTPException(status_code=400, detail="Only online delivery orders can be tracked.")
        
    # Verify phone number matches
    clean_db = re.sub(r'[\s\-]', '', sale.customer_phone or '')
    if clean_db.startswith('+237'): clean_db = clean_db[4:]
    elif clean_db.startswith('237'): clean_db = clean_db[3:]
    
    if clean_client != clean_db:
        raise HTTPException(
            status_code=400,
            detail="Invalid Verification Details: Phone number does not match this order."
        )
        
    return sale

@router.post("/{sale_id}/store-response", response_model=SaleOut)
def submit_store_response(
    sale_id: int,
    payload: StoreResponseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    POS Cashier/Proprietor endpoint: submit a counter-complain note response to a customer's dispute.
    """
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaction not found.")
        
    # Isolation: make sure owner/cashier belongs to this sale's enterprise
    if current_user.role != "technician" and sale.enterprise_id != current_user.enterprise_id:
        raise HTTPException(status_code=403, detail="Access Denied: Transaction belongs to another enterprise.")
        
    if sale.payment_status != "disputed":
        raise HTTPException(status_code=400, detail="Only disputed transactions can receive a store response.")
        
    sale.store_dispute_response = payload.store_response
    db.commit()
    db.refresh(sale)
    return sale


