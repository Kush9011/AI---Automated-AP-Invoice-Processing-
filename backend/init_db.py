"""
Initialize database with new multi-line schema.
Run this script to create all tables.
"""

from backend.db import Base, engine
import backend.models

# Drop existing tables (for fresh start)
Base.metadata.drop_all(bind=engine)

# Create new tables
Base.metadata.create_all(bind=engine)

print("✅ Database initialized successfully!")
print("")
print("Tables created:")
print("  📋 purchase_orders")
print("  📋 po_line_items")
print("  📋 goods_receipts")
print("  📋 gr_line_items")
print("  📋 invoice_staging")
print("  📋 invoice_line_items_staging")
print("  📋 invoice_final")
print("  📋 invoice_line_items_final")
print("")
print("Next: Run seed_data.py to populate test data")
