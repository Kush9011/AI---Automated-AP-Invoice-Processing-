"""
Seed data script for testing multi-line PO and GR matching.
Creates sample POs, GRs, and invoices with multiple line items.
"""

from backend.db import SessionLocal
from backend.models import (
    PurchaseOrder, POLineItem,
    GoodsReceipt, GRLineItem
)

db = SessionLocal()

# ============================================================
# SAMPLE PURCHASE ORDER 1 (Multi-line: 3 items)
# ============================================================

po1 = PurchaseOrder(
    po_number="PO-1001",
    vendor_id="VENDOR-001",
    po_date="2024-01-10"
)

po1_line_items = [
    POLineItem(
        po_number="PO-1001",
        item_number="001",
        description="Widget A - Premium",
        qty=10,
        unit_price=100.0
    ),
    POLineItem(
        po_number="PO-1001",
        item_number="002",
        description="Widget B - Standard",
        qty=5,
        unit_price=50.0
    ),
    POLineItem(
        po_number="PO-1001",
        item_number="003",
        description="Connector Kit",
        qty=20,
        unit_price=25.0
    )
]

db.add(po1)
for item in po1_line_items:
    db.add(item)

# ============================================================
# SAMPLE GOODS RECEIPT 1 (For PO-1001, Multi-line: 3 items)
# ============================================================

gr1 = GoodsReceipt(
    gr_id="GR-1001",
    po_number="PO-1001",
    gr_date="2024-01-12"
)

gr1_line_items = [
    GRLineItem(
        gr_id="GR-1001",
        po_number="PO-1001",
        item_number="001",
        description="Widget A - Premium",
        received_qty=10
    ),
    GRLineItem(
        gr_id="GR-1001",
        po_number="PO-1001",
        item_number="002",
        description="Widget B - Standard",
        received_qty=5
    ),
    GRLineItem(
        gr_id="GR-1001",
        po_number="PO-1001",
        item_number="003",
        description="Connector Kit",
        received_qty=20
    )
]

db.add(gr1)
for item in gr1_line_items:
    db.add(item)

# ============================================================
# SAMPLE PURCHASE ORDER 2 (Multi-line: 2 items)
# ============================================================

po2 = PurchaseOrder(
    po_number="PO-2001",
    vendor_id="VENDOR-002",
    po_date="2024-01-08"
)

po2_line_items = [
    POLineItem(
        po_number="PO-2001",
        item_number="001",
        description="Server Hardware",
        qty=2,
        unit_price=1500.0
    ),
    POLineItem(
        po_number="PO-2001",
        item_number="002",
        description="Network Cables - 100ft",
        qty=3,
        unit_price=75.0
    )
]

db.add(po2)
for item in po2_line_items:
    db.add(item)

# ============================================================
# SAMPLE GOODS RECEIPT 2 (For PO-2001, Multi-line: 2 items)
# ============================================================

gr2 = GoodsReceipt(
    gr_id="GR-2001",
    po_number="PO-2001",
    gr_date="2024-01-11"
)

gr2_line_items = [
    GRLineItem(
        gr_id="GR-2001",
        po_number="PO-2001",
        item_number="001",
        description="Server Hardware",
        received_qty=2
    ),
    GRLineItem(
        gr_id="GR-2001",
        po_number="PO-2001",
        item_number="002",
        description="Network Cables - 100ft",
        received_qty=3
    )
]

db.add(gr2)
for item in gr2_line_items:
    db.add(item)

# ============================================================
# COMMIT ALL
# ============================================================

db.commit()
db.close()

print("✅ Seed data created successfully!")
print("")
print("📦 Purchase Orders:")
print("  - PO-1001 (3 line items): Widget A, Widget B, Connector Kit")
print("  - PO-2001 (2 line items): Server Hardware, Network Cables")
print("")
print("📄 Goods Receipts:")
print("  - GR-1001 (for PO-1001, 3 line items)")
print("  - GR-2001 (for PO-2001, 2 line items)")
print("")
print("Now ready to test with multi-line invoices!")
