from pydantic import BaseModel # BaseModel is the base for all schemas
from typing import Optional # Optional means the field is not required
from datetime import datetime # for the created_at timestamp type

class ProductCreate(BaseModel):  # data shape when USER creates a product
    name: str # name is required
    description: Optional[str] = None # description is optional, defaults to None
    price: float # price is required
    stock: int = 0 # stock is optional, defaults to 0
    category: Optional[str] = None # category is optional
    image_url: Optional[str] = None # optional image link
    enterprise_id: Optional[int] = None # optional, backend can auto-fill

class ProductUpdate(BaseModel):  # data shape when USER updates a product (all fields optional)
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    enterprise_id: Optional[int] = None
    
class ProductOut(BaseModel): # data shape when WE send product back to user
    id: int # include the database ID
    name: str # product name
    description: Optional[str] # may or may not have description
    price: float # product price
    stock: int # current stock level
    category: Optional[str] # may or may not have category
    image_url: Optional[str] # may or may not have image link
    enterprise_id: int
    created_at: datetime # timestamp of when product was added
    
    class Config: # pydantic configuration
        from_attributes = True # allow reading data from SQLAlchemy model objects