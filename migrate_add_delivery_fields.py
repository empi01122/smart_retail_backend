"""
Safe migration: adds the new online-order / delivery columns to the sales table.
Run this ONCE with: python migrate_add_delivery_fields.py
It uses ALTER TABLE so existing sales data is preserved.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

COLUMNS_TO_ADD = [
    ("source",           "VARCHAR DEFAULT 'pos'"),
    ("customer_name",    "VARCHAR"),
    ("customer_phone",   "VARCHAR"),
    ("delivery_address", "VARCHAR"),
    ("order_note",       "VARCHAR"),
]

def migrate():
    for col_name, col_def in COLUMNS_TO_ADD:
        # Each column gets its own connection so a failure doesn't block the rest
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE sales ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                print(f"  [OK] Added column: {col_name}")
        except Exception as e:
            err = str(e)
            if "duplicate column" in err.lower() or "already exists" in err.lower():
                print(f"  [--] Skipped (already exists): {col_name}")
            else:
                print(f"  [ERR] {col_name}: {err[:120]}")
    print("\nMigration complete. Existing sales data was preserved.")

if __name__ == "__main__":
    migrate()
