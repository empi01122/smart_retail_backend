from sqlalchemy import Column, Integer, Float, DateTime  #importing coloumn types
from sqlalchemy.orm import relationship # lets us link tables together
from sqlalchemy.sql import func # gives us SQL functions like now()
from app.database import Base # the base class all models inherit from

class Sale(Base):   #define the Sale Table
    __tablename__= "sales" # actual table name in the database
    
    id = Column(Integer, primary_key=True, index=True) # unique ID for each sale
    total_amount = Column(Float, nullable=False) # total money for this sale
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # auto set time when sale is created
    
    items = relationship("SaleItem", back_populates="sale") # link to all items in this sale
    