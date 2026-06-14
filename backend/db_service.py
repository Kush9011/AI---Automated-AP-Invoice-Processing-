from backend.db import SessionLocal
from backend.models import (
    PurchaseOrder, POLineItem,
    GoodsReceipt, GRLineItem,
    InvoiceStaging, InvoiceLineItemStaging,
    InvoiceFinal, InvoiceLineItemFinal
)
from sqlalchemy.exc import IntegrityError
import uuid


# ============================================================
# CLEAR STAGING (Run before every invoice upload)
# ============================================================

def clear_invoice_staging():
    """
    ⚠️ IMPORTANT: Call this before every new invoice upload.
    Clears all rows from invoice_staging and invoice_line_items_staging.
    """
    db = SessionLocal()
    try:
        # Delete all staging records (cascade deletes line items)
        db.query(InvoiceStaging).delete()
        db.commit()
        print("✅ Invoice staging cleared")
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing staging: {e}")
    finally:
        db.close()


# ============================================================
# PURCHASE ORDER OPERATIONS (Multi-line)
# ============================================================

def get_po_with_items(db, po_number: str):
    """
    Retrieve PO with all its line items.
    Returns: PurchaseOrder object with line_items list
    """
    return db.query(PurchaseOrder).filter_by(po_number=po_number).first()


def get_po_line_item(db, po_number: str, item_number: str):
    """
    Retrieve specific line item from PO.
    Returns: POLineItem object or None
    """
    return db.query(POLineItem).filter_by(
        po_number=po_number,
        item_number=item_number
    ).first()


def get_all_po_line_items(db, po_number: str):
    """
    Retrieve all line items for a specific PO.
    Returns: List of POLineItem objects
    """
    return db.query(POLineItem).filter_by(po_number=po_number).all()


# ============================================================
# GOODS RECEIPT OPERATIONS (Multi-line)
# ============================================================

def get_gr_with_items(db, gr_id: str):
    """
    Retrieve GR with all its line items.
    Returns: GoodsReceipt object with line_items list
    """
    return db.query(GoodsReceipt).filter_by(gr_id=gr_id).first()


def get_gr_by_po(db, po_number: str):
    """
    Retrieve GR (and all line items) for a specific PO number.
    Returns: GoodsReceipt object or None
    """
    return db.query(GoodsReceipt).filter_by(po_number=po_number).first()


def get_gr_line_item(db, gr_id: str, item_number: str):
    """
    Retrieve specific line item from GR.
    Returns: GRLineItem object or None
    """
    return db.query(GRLineItem).filter_by(
        gr_id=gr_id,
        item_number=item_number
    ).first()


def get_all_gr_line_items(db, gr_id: str):
    """
    Retrieve all line items for a specific GR.
    Returns: List of GRLineItem objects
    """
    return db.query(GRLineItem).filter_by(gr_id=gr_id).all()


# ============================================================
# INVOICE STAGING OPERATIONS (Multi-line)
# ============================================================

def insert_staging(invoice_dict):
    """
    Insert multi-line invoice into staging.
    
    Expected format:
    {
        "invoice_id": "INV-123" (optional, generates UUID if missing),
        "po_number": "PO-1001",
        "vendor_id": "VENDOR-001",
        "invoice_date": "2024-01-15",
        "line_items": [
            {
                "item_number": "001",
                "description": "Widget A",
                "qty": 10,
                "unit_price": 100.0,
                "total_amount": 1000.0
            },
            {
                "item_number": "002",
                "description": "Widget B",
                "qty": 5,
                "unit_price": 50.0,
                "total_amount": 250.0
            }
        ]
    }
    """
    db = SessionLocal()
    
    try:
        # Generate invoice_id if not provided
        invoice_id = invoice_dict.get("invoice_id") or str(uuid.uuid4())
        
        # Create invoice staging record
        invoice = InvoiceStaging(
            invoice_id=invoice_id,
            po_number=invoice_dict.get("po_number"),
            vendor_id=invoice_dict.get("vendor_id"),
            invoice_date=invoice_dict.get("invoice_date"),
            status="PENDING"
        )
        
        db.add(invoice)
        
        # Insert all line items
        line_items = invoice_dict.get("line_items", [])
        for line_item in line_items:
            staging_line = InvoiceLineItemStaging(
                invoice_id=invoice_id,
                item_number=line_item.get("item_number"),
                po_number=invoice_dict.get("po_number"),
                description=line_item.get("description"),
                qty=line_item.get("qty"),
                unit_price=line_item.get("unit_price"),
                total_amount=line_item.get("total_amount")
            )
            db.add(staging_line)
        
        db.commit()
        
        print(f"✅ Invoice {invoice_id} inserted with {len(line_items)} line items")
        return invoice_id
        
    except IntegrityError as e:
        db.rollback()
        print(f"⚠️ Duplicate invoice: {invoice_dict.get('invoice_id')}")
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error inserting invoice: {e}")
        raise
    finally:
        db.close()


def get_invoice_with_items(db, invoice_id: str):
    """
    Retrieve invoice from staging with all line items.
    Returns: InvoiceStaging object with line_items list
    """
    return db.query(InvoiceStaging).filter_by(invoice_id=invoice_id).first()


def get_invoice_line_items(db, invoice_id: str):
    """
    Retrieve all line items for an invoice.
    Returns: List of InvoiceLineItemStaging objects
    """
    return db.query(InvoiceLineItemStaging).filter_by(invoice_id=invoice_id).all()


def update_invoice_status(db, invoice_id: str, status: str):
    """
    Update overall invoice status.
    status: PENDING, APPROVED, REJECTED, HOLD
    """
    invoice = db.query(InvoiceStaging).filter_by(invoice_id=invoice_id).first()
    if invoice:
        invoice.status = status
        db.commit()


# ============================================================
# INVOICE FINAL OPERATIONS (Multi-line)
# ============================================================

def move_invoice_to_final(db, invoice_id: str, match_results):
    """
    Move approved invoice from staging to final.
    Also records line-item level match status.
    
    match_results format:
    {
        "invoice_id": "...",
        "status": "APPROVED" / "REJECTED" / "HOLD",
        "line_items": [
            {
                "item_number": "001",
                "match_status": "PASS",
                ...
            }
        ]
    }
    """
    try:
        # Get staging invoice with all line items
        staging_invoice = db.query(InvoiceStaging).filter_by(
            invoice_id=invoice_id
        ).first()
        
        if not staging_invoice:
            raise ValueError(f"Invoice {invoice_id} not found in staging")
        
        # Create final invoice
        final_invoice = InvoiceFinal(
            invoice_id=invoice_id,
            po_number=staging_invoice.po_number,
            vendor_id=staging_invoice.vendor_id,
            invoice_date=staging_invoice.invoice_date,
            approval_status=match_results.get("status")
        )
        
        db.add(final_invoice)
        
        # Move line items from staging to final
        staging_line_items = db.query(InvoiceLineItemStaging).filter_by(
            invoice_id=invoice_id
        ).all()
        
        for staging_line in staging_line_items:
            # Find match result for this line item
            line_match_status = "APPROVED"  # Default
            for result_line in match_results.get("line_items", []):
                if result_line.get("item_number") == staging_line.item_number:
                    line_match_status = result_line.get("match_status", "APPROVED")
                    break
            
            final_line = InvoiceLineItemFinal(
                invoice_id=invoice_id,
                item_number=staging_line.item_number,
                po_number=staging_line.po_number,
                description=staging_line.description,
                qty=staging_line.qty,
                unit_price=staging_line.unit_price,
                total_amount=staging_line.total_amount,
                match_status=line_match_status
            )
            db.add(final_line)
        
        # Update staging status
        staging_invoice.status = "APPROVED"
        
        # Delete from staging
        db.query(InvoiceLineItemStaging).filter_by(invoice_id=invoice_id).delete()
        db.delete(staging_invoice)
        
        db.commit()
        print(f"✅ Invoice {invoice_id} moved to final")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error moving invoice to final: {e}")
        raise
