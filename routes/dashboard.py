from fastapi import APIRouter, Depends # APIRouter for grouping, Depends for DB  injections
from sqlalchemy.orm import Session # type hint for DB session
from sqlalchemy import func # SQL functions like count() and sum()

from app.database import get_db # provides a fresh DB session
from app.auth import get_current_user # Auth dependency
from models.user import User # User model
from models.sale import Sale # Sale model for querying sales 
from models.sale_item import SaleItem # Sale model for querying what was sold
from models.product import Product # Product model for stock info
from services.ai_service import generate_dashboard_insights # AI Insights Service

from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])  # all routes start with /dashboard

@router.get("/summary") # GET /dashboard/summary -> key business numbers
def get_dashboard_summary(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Resolve enterprise scoping
    target_ent_id = enterprise_id
    if current_user.role != "technician":
        target_ent_id = current_user.enterprise_id
    elif target_ent_id is None:
        # Default technician view to Enterprise 1 (Alpha) if not specified
        target_ent_id = 1

    total_sales = db.query(func.count(Sale.id)).filter(Sale.enterprise_id == target_ent_id).scalar()
    total_revenue = db.query(func.sum(Sale.total_amount)).filter(
        Sale.enterprise_id == target_ent_id,
        Sale.payment_status == "completed" # Only count fully finalized sales
    ).scalar() or 0.0
    
    total_products = db.query(func.count(Product.id)).filter(Product.enterprise_id == target_ent_id).scalar()
    low_stock = db.query(Product).filter(
        Product.enterprise_id == target_ent_id,
        Product.stock <= 5
    ).count()
    
    return {
        "total_sales": total_sales,
        "total_revenue": round(total_revenue, 2),
        "total_products": total_products,
        "low_stock_alerts": low_stock
    }
    
@router.get("/top-products") # GET /dashboard/top-products -> best selling products
def get_top_products(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    target_ent_id = enterprise_id
    if current_user.role != "technician":
        target_ent_id = current_user.enterprise_id
    elif target_ent_id is None:
        target_ent_id = 1

    results = (
        db.query(
            Product.name,
            func.sum(SaleItem.quantity).label("units_sold"),
            func.sum(SaleItem.quantity * SaleItem.unit_price).label("revenue")
        )
        .join(SaleItem, SaleItem.product_id == Product.id)
        .filter(Product.enterprise_id == target_ent_id)
        .group_by(Product.id)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(5)
        .all()
    )
    
    return [
        {"product": r.name, "units_sold": r.units_sold, "revenue": round(r.revenue, 2)}
        for r in results
    ]

@router.get("/insights") # GET /dashboard/insights -> AI generated store insights
def get_dashboard_insights_route(
    enterprise_id: Optional[int] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Fetch scoped statistics
    summary_data = get_dashboard_summary(enterprise_id, db, current_user)
    top_products_data = get_top_products(enterprise_id, db, current_user)
    
    # Hand to Gemini for insights
    ai_text = generate_dashboard_insights(summary_data, top_products_data)
    return {"insights": ai_text}