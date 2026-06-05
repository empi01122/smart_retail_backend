from pydantic import BaseModel # base class for all schemas
from typing import List # lets us say "a list of something"
from datetime import datetime # for the created_at timestamp
from schemas.sale_item import SaleItemCreate, SaleItemOut # reuse sale item schemas

from typing import List, Optional

from datetime import datetime

class SaleCreate(BaseModel): # data user sends when recording a sale
    items: List[SaleItemCreate] # a list of products being sold
    payment_method: Optional[str] = "cash" # cash or mobile_money
    enterprise_id: Optional[int] = None
    created_at: Optional[datetime] = None

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
    
    class Config: # pydantic config
        from_attributes = True # read data from SQLAlchemy objects

class DisputeResolve(BaseModel):
    action: str # "release" or "refund"