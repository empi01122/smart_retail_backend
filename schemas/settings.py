from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StoreSettingsBase(BaseModel):
    store_name: str
    logo_url: Optional[str] = None
    primary_theme_color: str
    secondary_theme_color: str
    accent_theme_color: str
    subscription_tier: str = "free"
    subscription_expires_at: Optional[datetime] = None
    theme_changes_count: int = 0

class StoreSettingsUpdate(BaseModel):
    # Everything is optional in an update; they can update just the name or just the color
    store_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_theme_color: Optional[str] = None
    secondary_theme_color: Optional[str] = None
    accent_theme_color: Optional[str] = None

class StoreSettingsResponse(StoreSettingsBase):
    id: int

    class Config:
        from_attributes = True # allows Pydantic to read SQLAlchemy database models

