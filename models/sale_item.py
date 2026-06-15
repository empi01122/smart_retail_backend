from sqlalchemy import Column, Integer, Float, ForeignKey # import column types + ForeignKey to link tables
from sqlalchemy.orm import relationship # lets us navigate between linked tables
from app.database import Base # base class every model must inherit

class SaleItem(Base): #one row = one product line inside a sale
    __tablename__ = "sale_items" # actual table name in the database
    
    id = Column(Integer, primary_key=True, index=True) # unique ID for each sale item
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False) # which sale this item belongs to
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False) # which product was sold
    quantity = Column(Integer, nullable=False, default=1) # how many units were sold
    unit_price = Column(Float, nullable=False) # a price of product at the time of sale
    
    sale = relationship("Sale", back_populates="items") # navigate from item back to its sale
    product = relationship("Product") # navigate from item to its product

    @property
    def product_name(self):
        return self.product.name if self.product else None

    @property
    def image_url(self):
        return self.product.image_url if self.product else None

    @property
    def category(self):
        return self.product.category if self.product else None