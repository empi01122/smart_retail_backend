import sys
sys.path.append(r'c:\Users\MP\Desktop\School project\smart-retail-system_Backend')

from app.database import SessionLocal
from models.enterprise import Enterprise
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem
from schemas.sale import SaleCreate
from services.business_logic import create_sale_with_stock_update

db = SessionLocal()
try:
    sale_data = SaleCreate(
        items=[{"product_id": 1, "quantity": 1}],
        payment_method="cash",
        source="pos"
    )
    print("Testing create_sale_with_stock_update...")
    # Rollback is automatic if it fails
    sale = create_sale_with_stock_update(db, sale_data, enterprise_id=1)
    print(f"Success! Created sale ID: {sale.id}")
except Exception as e:
    import traceback
    print("Error occurred:")
    traceback.print_exc()
finally:
    db.rollback()
    db.close()
