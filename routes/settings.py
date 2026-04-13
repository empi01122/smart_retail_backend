from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

from models.settings import StoreSettings
from schemas.settings import StoreSettingsResponse, StoreSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/", response_model=StoreSettingsResponse)
def get_store_settings(db: Session = Depends(get_db)):
    """
    Fetches the global store settings. 
    If no settings currently exist, it safely creates a default setup so the frontend never crashes.
    """
    settings = db.query(StoreSettings).first() # Grab the first (and only) settings row
    
    if not settings:
        # Generate the default settings if they don't exist yet
        settings = StoreSettings(
            store_name="Smart Retail Shop",
            primary_theme_color="#4F46E5", # Beautiful Indigo
            secondary_theme_color="#F8FAFC" # Soft Slate
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings

@router.put("/", response_model=StoreSettingsResponse)
def update_store_settings(settings_update: StoreSettingsUpdate, db: Session = Depends(get_db)):
    """
    Updates the global store branding. This allows the frontend to change colors/names dynamically.
    """
    settings = db.query(StoreSettings).first()
    
    if not settings:
        # In the rare event they try to update before fetching, create it first
        settings = StoreSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    # Safely apply only the fields they provided in the request
    update_data = settings_update.dict(exclude_unset=True) # Ignore blank/None fields
    for key, value in update_data.items():
        setattr(settings, key, value)
        
    db.commit()
    db.refresh(settings) # fetch the updated data from DB
    
    return settings
