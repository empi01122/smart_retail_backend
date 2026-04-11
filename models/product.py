from sqlalchemy import Column, Integer, String, Float, DateTime #omport column data types
from sqlalchemy.sql import func # gives us SQL functions like now()
from app.database import Base # base class that all models must inherit from


class Product(Base):  #defines the product table as a python class
    __tablename__ = "products" #actual name of the table in the database
    
    id = Column(Integer, primary_key=True, index=True) # unique ID, auto-increments
    name = Column(String, nullable=False) # product name, cannot be empty
    description = Column(String, nullable=True) # optional product description
    price = Column(Float, nullable=False)  # selling price, required
    stock = Column(Integer, default=0) # quantity in stock, starts at 0
    category = Column(String, nullable=True) #optional category e.g. "drinks", "snacks"
    image_url = Column(String, nullable=True) #optional image link for the frontend
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # auto-set when product is created
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # auto-update whenever product changes
 