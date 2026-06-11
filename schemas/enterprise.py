from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EnterpriseBase(BaseModel):
    name: str
    logo_url: Optional[str] = None
    primary_theme_color: str = "#4F46E5"
    secondary_theme_color: str = "#F8FAFC"
    accent_theme_color: str = "#F59E0B"
    is_premium: bool = False
    subscription_tier: str = "free"
    subscription_expires_at: Optional[datetime] = None
    theme_changes_count: int = 0

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseUpdate(BaseModel):
    name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_theme_color: Optional[str] = None
    secondary_theme_color: Optional[str] = None
    accent_theme_color: Optional[str] = None
    is_premium: Optional[bool] = None
    subscription_tier: Optional[str] = None
    subscription_expires_at: Optional[datetime] = None
    theme_changes_count: Optional[int] = None

class EnterpriseResponse(EnterpriseBase):
    id: int

    class Config:
        from_attributes = True

class EnterpriseUpgradeMomo(BaseModel):
    phone: str
    tier: str


class ReviewCreate(BaseModel):
    customer_name: str
    rating: int
    comment: str


class ReviewResponse(BaseModel):
    id: int
    enterprise_id: int
    customer_name: str
    rating: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True



