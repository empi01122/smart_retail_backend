from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Boolean
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
    is_confirmed = Column(Boolean, default=False) # Cashier order confirmation / dispatch tracker
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Online order / delivery fields
    source = Column(String, default="pos") # "pos" = in-store, "online" = public catalog order
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    delivery_address = Column(String, nullable=True)
    order_note = Column(String, nullable=True)
    
    # Dispute details for escrow arbitration
    dispute_reason = Column(String, nullable=True)
    dispute_picture = Column(String, nullable=True)
    store_dispute_response = Column(String, nullable=True)
    
    # Relationships
    enterprise = relationship("Enterprise")
    items = relationship("SaleItem", back_populates="sale")

    @property
    def receipt_number(self):
        from datetime import datetime
        year = self.created_at.year if (self.created_at and hasattr(self.created_at, 'year')) else datetime.now().year
        id_str = str(self.id).zfill(4) if self.id is not None else "XXXX"
        
        ent_code = "ENT"
        if self.enterprise_id == 1:
            ent_code = "ENTA"
        elif self.enterprise_id == 2:
            ent_code = "ENTB"
        elif self.enterprise_id == 3:
            ent_code = "ENTC"
        else:
            # Dynamic fallback for new enterprise IDs
            offset = (self.enterprise_id - 1) % 26 if self.enterprise_id else 0
            letter = chr(65 + offset)
            ent_code = f"ENT{letter}"
            
        return f"PDT{ent_code}{year}{id_str}"

    