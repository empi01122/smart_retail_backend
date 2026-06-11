from pydantic import BaseModel # base class for all schemas
from typing import List, Optional
from datetime import datetime
from schemas.sale_item import SaleItemCreate, SaleItemOut # reuse sale item schemas

class SaleCreate(BaseModel): # data user sends when recording a sale
    items: List[SaleItemCreate] # a list of products being sold
    payment_method: Optional[str] = "cash" # cash or mobile_money
    enterprise_id: Optional[int] = None
    created_at: Optional[datetime] = None
    # Online / delivery order fields (optional for in-store POS)
    source: Optional[str] = "pos"          # "pos" or "online"
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    order_note: Optional[str] = None

class SaleOut(BaseModel): # data we send back after a sale is recorded
    id: int # sale ID from the database
    receipt_number: Optional[str] = None
    total_amount: float # total price calculated by backend
    payment_status: str # completed, pending, paid_escrow, refunded
    payment_method: str
    delivery_pin: Optional[str] = None # 4-digit PIN (returned if escrow)
    enterprise_id: int
    created_at: datetime # when the sale happened
    items: List[SaleItemOut] # all the items in this sale
    is_confirmed: Optional[bool] = False
    # Online / delivery order fields
    source: Optional[str] = "pos"
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    order_note: Optional[str] = None
    
    # Dispute details for escrow arbitration
    dispute_reason: Optional[str] = None
    dispute_picture: Optional[str] = None
    store_dispute_response: Optional[str] = None

    class Config: # pydantic config
        from_attributes = True # read data from SQLAlchemy objects

class PublicDisputeRequest(BaseModel):
    customer_phone: str
    delivery_pin: str
    dispute_reason: str
    dispute_picture: Optional[str] = None

class StoreResponseRequest(BaseModel):
    store_response: str

class DisputeResolve(BaseModel):
    action: str # "release" or "refund"