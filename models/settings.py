from sqlalchemy import Column, Integer, String
from app.database import Base

class StoreSettings(Base):
    __tablename__ = "store_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String, default="Smart Retail Shop")
    logo_url = Column(String, nullable=True) # Nullable because they might not upload a logo
    
    # We use a beautiful default Indigo (#4F46E5) instead of a robotic blue or black
    primary_theme_color = Column(String, default="#4F46E5") 
    
    # A soft, elegant slate/off-white for secondary backgrounds or accents
    secondary_theme_color = Column(String, default="#F8FAFC") 
