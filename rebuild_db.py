import sys
import os

# Add current directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from models.enterprise import Enterprise
from models.user import User
from models.product import Product
from models.sale import Sale
from models.sale_item import SaleItem

def rebuild_db():
    print("WARNING: Rebuilding database will destroy all current tables and data!")
    print("Dropping all existing tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating all tables from scratch...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding default Enterprises...")
        # 1. Seed the 3 default enterprises
        alpha = Enterprise(
            id=1,
            name="Enterprise Alpha",
            primary_theme_color="#4F46E5", # Indigo
            secondary_theme_color="#F8FAFC",
            accent_theme_color="#F59E0B",
            is_premium=False
        )
        beta = Enterprise(
            id=2,
            name="Enterprise Beta",
            primary_theme_color="#059669", # Emerald
            secondary_theme_color="#F0FDF4",
            accent_theme_color="#D97706",
            is_premium=True # Seed Beta as premium for testing
        )
        gamma = Enterprise(
            id=3,
            name="Enterprise Gamma",
            primary_theme_color="#0F172A", # Midnight Dark
            secondary_theme_color="#1E293B",
            accent_theme_color="#06B6D4",
            is_premium=True # Seed Gamma as premium for testing
        )
        
        db.add(alpha)
        db.add(beta)
        db.add(gamma)
        db.commit()
        
        print("Seeding mock Technician user...")
        # 2. Seed mock technician/developer user for bypass mode
        technician = User(
            clerk_id="mock_local_admin_clerk_id",
            name="Local System Technician",
            email="admin@smartretail.com",
            role="technician",
            enterprise_id=None # Technician has global access
        )
        db.add(technician)
        
        print("Seeding mock Proprietor users...")
        # Proprietor for Enterprise Alpha
        prop_alpha = User(
            clerk_id="mock_proprietor_alpha",
            name="Alpha Proprietor",
            email="proprietor_alpha@smartretail.com",
            role="proprietor",
            enterprise_id=1
        )
        # Employee for Enterprise Alpha
        emp_alpha = User(
            clerk_id="mock_employee_alpha",
            name="Alpha Cashier",
            email="cashier_alpha@smartretail.com",
            role="employee",
            enterprise_id=1
        )
        db.add(prop_alpha)
        db.add(emp_alpha)
        db.commit()
        
        print("Seeding sample Products for each Enterprise...")
        # Products for Enterprise Alpha (Grocery/Snacks themed)
        products_alpha = [
            Product(name="premium organic milk", price=1500.0, stock=20, category="Dairy", enterprise_id=1),
            Product(name="crusty fresh baguette", price=500.0, stock=30, category="Bakery", enterprise_id=1),
            Product(name="dark roast coffee beans", price=3500.0, stock=8, category="Beverages", enterprise_id=1),
            Product(name="crispy sea salt potato chips", price=800.0, stock=50, category="Snacks", enterprise_id=1),
        ]
        
        # Products for Enterprise Beta (Health & Pharmacy themed)
        products_beta = [
            Product(name="multivitamin formula 90ct", price=8500.0, stock=15, category="Vitamins", enterprise_id=2),
            Product(name="organic lavender soap bar", price=2000.0, stock=40, category="Personal Care", enterprise_id=2),
            Product(name="extra strength pain relief", price=3000.0, stock=2, category="Pharmacy", enterprise_id=2),
        ]
        
        # Products for Enterprise Gamma (Gaming/Electronics themed)
        products_gamma = [
            Product(name="mechanical keyboard rgb", price=45000.0, stock=5, category="Electronics", enterprise_id=3),
            Product(name="wireless precision gaming mouse", price=25000.0, stock=12, category="Electronics", enterprise_id=3),
            Product(name="usb-c fast charging cable", price=5000.0, stock=25, category="Accessories", enterprise_id=3),
        ]
        
        for p in products_alpha + products_beta + products_gamma:
            db.add(p)
            
        db.commit()
        print("Database rebuilt and seeded successfully! Ready for multi-enterprise testing.")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_db()
