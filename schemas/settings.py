from pydantic import BaseModel
from typing import Optional

class StoreSettingsBase(BaseModel):
    store_name: str
    logo_url: Optional[str] = None
    primary_theme_color: str
    secondary_theme_color: str

class StoreSettingsUpdate(BaseModel):
    # Everything is optional in an update; they can update just the name or just the color
    store_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_theme_color: Optional[str] = None
    secondary_theme_color: Optional[str] = None

class StoreSettingsResponse(StoreSettingsBase):
    id: int

    class Config:
        from_attributes = True # allows Pydantic to read SQLAlchemy database models
