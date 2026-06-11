"""
Safe migration: adds subscription-related columns to the enterprises table.
Run this ONCE with: python migrate_add_subscription_fields.py
It uses ALTER TABLE so existing enterprise data is preserved.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from sqlalchemy import text

COLUMNS_TO_ADD = [
    ("subscription_tier",       "VARCHAR DEFAULT 'free'"),
    ("subscription_expires_at", "TIMESTAMP"),
    ("theme_changes_count",     "INTEGER DEFAULT 0"),
]

def migrate():
    print("Running subscription fields migration on enterprises table...")
    for col_name, col_def in COLUMNS_TO_ADD:
        try:
            with engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE enterprises ADD COLUMN {col_name} {col_def}"))
                conn.commit()
                print(f"  [OK] Added column: {col_name}")
        except Exception as e:
            err = str(e)
            if "duplicate column" in err.lower() or "already exists" in err.lower():
                print(f"  [--] Skipped (already exists): {col_name}")
            else:
                print(f"  [ERR] {col_name}: {err[:120]}")
    print("\nMigration complete. Existing enterprise data was preserved.")

if __name__ == "__main__":
    migrate()
