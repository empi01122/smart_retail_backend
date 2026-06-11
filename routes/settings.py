from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.auth import get_current_user, get_admin_user # Auth dependencies
from models.user import User # User model
from models.enterprise import Enterprise
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
def get_store_settings(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Fetches the settings for the scoped enterprise. 
    """
    target_ent_id = enterprise_id
    if current_user.role != "technician":
        target_ent_id = current_user.enterprise_id
    elif target_ent_id is None:
        target_ent_id = 1
        
    ent = db.query(Enterprise).filter(Enterprise.id == target_ent_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise settings not found.")

    return StoreSettingsResponse(
        id=ent.id,
        store_name=ent.name,
        logo_url=ent.logo_url,
        primary_theme_color=ent.primary_theme_color,
        secondary_theme_color=ent.secondary_theme_color,
        accent_theme_color=ent.accent_theme_color,
        subscription_tier=ent.subscription_tier or "free",
        subscription_expires_at=ent.subscription_expires_at,
        theme_changes_count=ent.theme_changes_count or 0
    )

@router.put("/", response_model=StoreSettingsResponse)
def update_store_settings(
    settings_update: StoreSettingsUpdate, 
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    Updates the visual branding for the enterprise.
    """
    target_ent_id = enterprise_id
    if admin.role != "technician":
        target_ent_id = admin.enterprise_id
    elif target_ent_id is None:
        target_ent_id = 1
        
    ent = db.query(Enterprise).filter(Enterprise.id == target_ent_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found.")
        
    update_data = settings_update.model_dump(exclude_unset=True)
    if "store_name" in update_data:
        ent.name = update_data["store_name"]
    if "logo_url" in update_data:
        ent.logo_url = update_data["logo_url"]
    if "primary_theme_color" in update_data:
        ent.primary_theme_color = update_data["primary_theme_color"]
    if "secondary_theme_color" in update_data:
        ent.secondary_theme_color = update_data["secondary_theme_color"]
    if "accent_theme_color" in update_data:
        ent.accent_theme_color = update_data["accent_theme_color"]
        
    db.commit()
    db.refresh(ent)
    
    return StoreSettingsResponse(
        id=ent.id,
        store_name=ent.name,
        logo_url=ent.logo_url,
        primary_theme_color=ent.primary_theme_color,
        secondary_theme_color=ent.secondary_theme_color,
        accent_theme_color=ent.accent_theme_color,
        subscription_tier=ent.subscription_tier or "free",
        subscription_expires_at=ent.subscription_expires_at,
        theme_changes_count=ent.theme_changes_count or 0
    )

@router.get("/themes")
def list_curated_themes(current_user: User = Depends(get_current_user)):
    """
    Retrieves the list of curated color palettes for the store branding.
    """
    return [{"id": key, **value} for key, value in CURATED_THEMES.items()]

@router.post("/themes/{theme_id}/apply", response_model=StoreSettingsResponse)
def apply_curated_theme(
    theme_id: str, 
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    admin: User = Depends(get_admin_user)
):
    """
    Instantly applies a pre-defined theme to the enterprise's branding.
    """
    if theme_id not in CURATED_THEMES:
        raise HTTPException(status_code=400, detail="Invalid theme selection. Theme does not exist.")
        
    target_ent_id = enterprise_id
    if admin.role != "technician":
        target_ent_id = admin.enterprise_id
    elif target_ent_id is None:
        target_ent_id = 1
        
    theme = CURATED_THEMES[theme_id]
    ent = db.query(Enterprise).filter(Enterprise.id == target_ent_id).first()
    if not ent:
        raise HTTPException(status_code=404, detail="Enterprise not found.")
        
    if admin.role != "technician":
        tier = ent.subscription_tier or "free"
        if tier == "free":
            raise HTTPException(
                status_code=403,
                detail="Applying curated branding themes is a premium feature. Please upgrade to Pro or Ultra."
            )
        elif tier == "pro":
            if ent.theme_changes_count >= 1:
                raise HTTPException(
                    status_code=403,
                    detail="Pro subscription is limited to exactly 1 theme customization edit. Upgrade to Ultra for unlimited edits."
                )
            ent.theme_changes_count += 1
        
    ent.primary_theme_color = theme["primary_theme_color"]
    ent.secondary_theme_color = theme["secondary_theme_color"]
    ent.accent_theme_color = theme["accent_theme_color"]
    
    db.commit()
    db.refresh(ent)
    
    return StoreSettingsResponse(
        id=ent.id,
        store_name=ent.name,
        logo_url=ent.logo_url,
        primary_theme_color=ent.primary_theme_color,
        secondary_theme_color=ent.secondary_theme_color,
        accent_theme_color=ent.accent_theme_color,
        subscription_tier=ent.subscription_tier or "free",
        subscription_expires_at=ent.subscription_expires_at,
        theme_changes_count=ent.theme_changes_count or 0
    )

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
