from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Sale(Base):
    __tablename__= "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String, default="completed") # completed, pending, paid_escrow, refunded
    payment_method = Column(String, nullable=False, default="cash") # cash or mobile_money
    delivery_pin = Column(String, nullable=True) # 4-digit OTP for escrow release
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    enterprise = relationship("Enterprise")
    items = relationship("SaleItem", back_populates="sale")

    @property
    def receipt_number(self):
        from datetime import datetime
        year = self.created_at.year if (self.created_at and hasattr(self.created_at, 'year')) else datetime.now().year
        id_str = str(self.id).zfill(4) if self.id is not None else "XXXX"
        return f"PDT{year}{id_str}"
    