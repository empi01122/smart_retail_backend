from sqlalchemy import Column, Integer, String
from app.database import Base

class StoreSettings(Base):
    __tablename__ = "store_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String, default="Smart Retail Shop")
    logo_url = Column(String, nullable=True) # Nullable because they might not upload a logo
    
    # We use a beautiful default Indigo (#4F46E5) - representing trust, quality, and stability
    primary_theme_color = Column(String, default="#4F46E5") 
    
    # A soft, modern slate (#F8FAFC) - providing a clean, light, and open canvas
    secondary_theme_color = Column(String, default="#F8FAFC") 
    
    # An inviting warm Amber (#F59E0B) - representing friendly hospitality, hospitality, and warning highlights
    accent_theme_color = Column(String, default="#F59E0B")
