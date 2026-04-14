from pydantic import BaseModel # base class for all schemas
from typing import List # lets us say "a list of something"
from datetime import datetime # for the created_at timestamp
from schemas.sale_item import SaleItemCreate, SaleItemOut # reuse sale item schemas

class SaleCreate(BaseModel): # data user sends when recording a sale
    items: List[SaleItemCreate] # a list of products being sold
    
class SaleOut(BaseModel): # data we send back after a sale is recorded
    id: int # sale ID from the database
    total_amount: float # total price calculated by backend
    created_at: datetime # when the sale happened
    items: List[SaleItemOut] # all the items in this sale
    
    class Config: # pydantic config
        from_attributes = True # read data from SQLAlchemy objects