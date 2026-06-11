import sys
sys.path.append(r'c:\Users\MP\Desktop\School project\smart-retail-system_Backend')

from app.database import SessionLocal
from models.enterprise import Enterprise
from models.user import User

db = SessionLocal()
try:
    users = db.query(User).all()
    print("--- Users in DB ---")
    for u in users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role}, EntID: {u.enterprise_id}")
    print("------------------------")
finally:
    db.close()
