import sys
sys.path.append(r'c:\Users\MP\Desktop\School project\smart-retail-system_Backend')

from app.database import SessionLocal
from models.enterprise import Enterprise
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem

db = SessionLocal()
try:
    sales = db.query(Sale).order_by(Sale.created_at.desc()).limit(10).all()
    print("--- Recent Sales ---")
    for s in sales:
        print(f"ID: {s.id}, Total: {s.total_amount}, Status: {s.payment_status}, Method: {s.payment_method}, Source: {s.source}, CreatedAt: {s.created_at}")
        items = db.query(SaleItem).filter(SaleItem.sale_id == s.id).all()
        for item in items:
            p = db.query(Product).filter(Product.id == item.product_id).first()
            pname = p.name if p else "Unknown"
            print(f"  Item: {pname} (ID: {item.product_id}), Qty: {item.quantity}, Price: {item.unit_price}")
    print("------------------------")
finally:
    db.close()
