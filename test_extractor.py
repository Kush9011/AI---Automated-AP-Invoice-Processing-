from sqlalchemy import text
from backend.db import SessionLocal

def clear_invoice_staging():

    db = SessionLocal()

    print("\n⚠️ Clearing invoice staging tables...\n")

    tables = [
        "invoice_line_items_staging",
        "invoice_staging"
    ]

    for table in tables:

        try:
            db.execute(text(f"DELETE FROM {table}"))
            print(f"✅ Cleared {table}")

        except Exception as e:
            print(f"❌ Error clearing {table}: {e}")

    db.commit()
    db.close()

    print("\n🎯 Invoice staging cleared successfully!")


if __name__ == "__main__":
    clear_invoice_staging()