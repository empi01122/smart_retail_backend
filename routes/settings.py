from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, get_admin_user # Auth dependencies
from models.user import User # User model
from models.settings import StoreSettings
from schemas.settings import StoreSettingsResponse, StoreSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

# Curated, extravagantly beautiful color-psychology themes
CURATED_THEMES = {
    "indigo_trust": {
        "name": "Trust & Stability (Indigo & Amber)",
        "description": "A premium, reliable theme for corporate retail, supermarkets, and standard storefronts.",
        "primary_theme_color": "#4F46E5",
        "secondary_theme_color": "#F8FAFC",
        "accent_theme_color": "#F59E0B"
    },
    "emerald_organic": {
        "name": "Growth & Organic (Emerald & Mint)",
        "description": "Perfect for organic grocers, pharmacies, flower shops, and health-focused retail.",
        "primary_theme_color": "#059669",
        "secondary_theme_color": "#F0FDF4",
        "accent_theme_color": "#D97706"
    },
    "rose_luxury": {
        "name": "Luxury & Boutique (Deep Rose & Teal)",
        "description": "A high-fashion, cosmetics, and luxury boutique theme designed to look highly sophisticated.",
        "primary_theme_color": "#BE185D",
        "secondary_theme_color": "#FFF1F2",
        "accent_theme_color": "#0D9488"
    },
    "amber_sunset": {
        "name": "Bakery & Cafe (Warm Amber & Royal)",
        "description": "Warm, welcoming tones designed for bakeries, coffee shops, and cozy establishments.",
        "primary_theme_color": "#D97706",
        "secondary_theme_color": "#FEF3C7",
        "accent_theme_color": "#2563EB"
    },
    "midnight_cyber": {
        "name": "Midnight Tech (Dark Slate & Neon Cyan)",
        "description": "An ultra-modern theme tailored for gaming hubs, electronic stores, and sleek night themes.",
        "primary_theme_color": "#0F172A",
        "secondary_theme_color": "#1E293B",
        "accent_theme_color": "#06B6D4"
    }
}

@router.get("/", response_model=StoreSettingsResponse)
def get_store_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Fetches the global store settings. 
    If no settings currently exist, it safely creates a default setup so the frontend never crashes.
    """
    settings = db.query(StoreSettings).first() # Grab the first (and only) settings row
    
    if not settings:
        # Generate the default settings if they don't exist yet
        settings = StoreSettings(
            store_name="Smart Retail Shop",
            primary_theme_color="#4F46E5", # Beautiful Trustworthy Indigo
            secondary_theme_color="#F8FAFC", # Modern Clean Slate
            accent_theme_color="#F59E0B" # Inviting Warm Amber
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings

@router.put("/", response_model=StoreSettingsResponse)
def update_store_settings(settings_update: StoreSettingsUpdate, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
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
    update_data = settings_update.model_dump(exclude_unset=True) # Ignore blank/None fields
    for key, value in update_data.items():
        setattr(settings, key, value)
        
    db.commit()
    db.refresh(settings) # fetch the updated data from DB
    
    return settings

@router.get("/themes")
def list_curated_themes(current_user: User = Depends(get_current_user)):
    """
    Retrieves the list of curated color palettes for the store branding.
    """
    return [{"id": key, **value} for key, value in CURATED_THEMES.items()]

@router.post("/themes/{theme_id}/apply", response_model=StoreSettingsResponse)
def apply_curated_theme(theme_id: str, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    """
    Instantly applies a pre-defined, high-quality visual theme to your store branding.
    """
    if theme_id not in CURATED_THEMES:
        raise HTTPException(status_code=400, detail="Invalid theme selection. Theme does not exist.")
        
    theme = CURATED_THEMES[theme_id]
    settings = db.query(StoreSettings).first()
    
    if not settings:
        settings = StoreSettings()
        db.add(settings)
        
    settings.primary_theme_color = theme["primary_theme_color"]
    settings.secondary_theme_color = theme["secondary_theme_color"]
    settings.accent_theme_color = theme["accent_theme_color"]
    
    db.commit()
    db.refresh(settings)
    return settings

# Curated, top-notch external theme generators to recommend to store owners
EXTERNAL_INSPIRATION_TOOLS = [
    {
        "name": "Happy Hues",
        "url": "https://www.happyhues.co",
        "description": "See beautiful, pre-curated color palettes applied directly to a mock website in real-time, with color psychology explanations."
    },
    {
        "name": "Realtime Colors",
        "url": "https://realtimecolors.com",
        "description": "Generate gorgeous random color palettes and instantly preview how they look on live dashboards, landing pages, and visual cards."
    },
    {
        "name": "Coolors",
        "url": "https://coolors.co",
        "description": "The industry standard for palette generation. Generate millions of premium palettes by pressing the spacebar, then export as JSON."
    }
]

@router.get("/inspiration")
def get_external_theme_inspiration(current_user: User = Depends(get_current_user)):
    """
    Retrieves the list of recommended external palette generators to help users discover top-notch brand colors.
    """
    return EXTERNAL_INSPIRATION_TOOLS
