from pydantic import BaseModel # BaseModel is what all schemas inherit from

class SaleItemCreate(BaseModel): # shape of data when CREATING a sale item (sent by user)
    product_id: int # user must provide which product
    quantity: int # user must provide how many
    
class SaleItemOut(BaseModel): # shape of data when RETURNING a sale item (sent to user)
    id: int # include the DB-generated ID
    product_id: int # which product was sold
    quantity: int # how many were sold
    unit_price: float # price at time of sale
    
    class Config: # pydantic config class
        from_attributes = True # allows reading data from SQLAlchemy model objects