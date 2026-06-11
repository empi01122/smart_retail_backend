from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.database import Base

class Enterprise(Base):
    __tablename__ = "enterprises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    
    # Beautiful visual themes
    primary_theme_color = Column(String, default="#4F46E5") 
    secondary_theme_color = Column(String, default="#F8FAFC") 
    accent_theme_color = Column(String, default="#F59E0B")
    
    # Premium subscription features lock
    is_premium = Column(Boolean, default=False)
    
    # New subscription monetization columns
    subscription_tier = Column(String, default="free")  # "free" | "pro" | "ultra"
    subscription_expires_at = Column(DateTime, nullable=True)
    theme_changes_count = Column(Integer, default=0)


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    customer_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)



