from pydantic import BaseModel
from typing import Optional

class EnterpriseBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    primary_theme_color: str = "#4F46E5"
    secondary_theme_color: str = "#F8FAFC"
    accent_theme_color: str = "#F59E0B"
    is_premium: bool = False

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_theme_color: Optional[str] = None
    secondary_theme_color: Optional[str] = None
    accent_theme_color: Optional[str] = None
    is_premium: Optional[bool] = None

class EnterpriseResponse(EnterpriseBase):
    id: int

    class Config:
        from_attributes = True
