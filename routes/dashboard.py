from fastapi import APIRouter, Depends # APIRouter for grouping, Depends for DB  injections
from sqlalchemy.orm import Session # type hint for DB session
from sqlalchemy import func # SQL functions like count() and sum()

from app.database import get_db # provides a fresh DB session
from models.sale import Sale # Sale model for querying sales 
from models.sale_item import SaleItem # Sale model for querying what was sold
from models.product import Product # Product model for stock info
from services.ai_service import generate_dashboard_insights # AI Insights Service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])  # all routes start with /dashboard

@router.get("/summary") # GET /dashboard/summary -> key business numbers
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_sales = db.query(func.count(Sale.id)).scalar() # count total number of sales
    total_revenue = db.query(func.sum(Sale.total_amount)).scalar() or 0.0 # sum all sale amounts, default 0
    total_products = db.query(func.count(Product.id)).scalar() # count total products
    low_stock = db.query(Product).filter(Product.stock <= 5).count() # products with 5 fewer units left
    
    return { # return as a simple dictionary (FastAPI converts to JSON)
            "total_sales": total_sales, # how many sales have been made
            "total_revenue": round(total_revenue, 2), # total money earned, rounded to 2 decimals
            "total_products": total_products, # how many products exist
            "low_stock_alerts": low_stock # how many products are running low
            }
    
@router.get("/top-products") # GET /dashboard/top-products -> best selling products
def get_top_products(db: Session = Depends(get_db)):
    results = (
        db.query(
            Product.name, # get product name
            func.sum(SaleItem.quantity).label("units_sold"), # total units sold per product
            func.sum(SaleItem.quantity * SaleItem.unit_price).label("revenue") # total revenue per product
        )
        .join(SaleItem, SaleItem.product_id == Product.id) # join products with their sale items
        .group_by(Product.id) # group results by product
        .order_by(func.sum(SaleItem.quantity).desc()) # sort by most sold first
        .limit(5) # only return top 5 products
        .all()
    )
    
    return [ # build and return a clean list
        {"product": r.name, "units_sold": r.units_sold, "revenue": round(r.revenue, 2)}
        for r in results # loop through each result row
    ]

@router.get("/insights") # GET /dashboard/insights -> AI generated store insights
def get_dashboard_insights_route(db: Session = Depends(get_db)):
    # 1. Fetch exactly what the dashboard shows naturally
    summary_data = get_dashboard_summary(db)
    top_products_data = get_top_products(db)
    
    # 2. Hand it directly to Gemini for formatting to english text
    ai_text = generate_dashboard_insights(summary_data, top_products_data)
    
    # 3. Return the result back to the frontend
    return {"insights": ai_text}