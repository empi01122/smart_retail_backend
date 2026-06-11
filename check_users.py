import sys
sys.path.append(r'c:\Users\MP\Desktop\School project\smart-retail-system_Backend')

from app.database import SessionLocal
from models.enterprise import Enterprise
from models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print("--- Users ---")
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}, EnterpriseID: {u.enterprise_id}")
    print("--- Enterprises ---")
    ents = db.query(Enterprise).all()
    for e in ents:
        print(f"ID: {e.id}, Name: {e.name}, SubType: {e.subscription_type if hasattr(e, 'subscription_type') else 'None'}")
finally:
    db.close()
