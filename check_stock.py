import sys
sys.path.append(r'c:\Users\MP\Desktop\School project\smart-retail-system_Backend')

from app.database import SessionLocal
from models.enterprise import Enterprise
from models.product import Product
from models.user import User
from models.sale import Sale
from models.sale_item import SaleItem

db = SessionLocal()
try:
    products = db.query(Product).all()
    print("--- Products in DB ---")
    for p in products:
        print(f"ID: {p.id}, Name: {p.name}, Stock: {p.stock}, Price: {p.price}, EnterpriseID: {p.enterprise_id}")
    print("------------------------")
finally:
    db.close()
