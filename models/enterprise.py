from sqlalchemy import Column, Integer, String, Boolean
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
