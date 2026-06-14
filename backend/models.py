from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base


class PurchaseOrder(Base):
    """
    Multi-line Purchase Order.
    Each PO can have multiple line items.
    """
    __tablename__ = "purchase_orders"

    po_number = Column(String, primary_key=True)
    vendor_id = Column(String)  # Optional: vendor reference
    po_date = Column(String)     # Optional: PO date
    
    # Relationship to line items
    line_items = relationship("POLineItem", back_populates="purchase_order", cascade="all, delete-orphan")


class POLineItem(Base):
    """
    Line item within a Purchase Order.
    Composite key: po_number + item_number
    """
    __tablename__ = "po_line_items"

    po_number = Column(String, ForeignKey("purchase_orders.po_number"), primary_key=True)
    item_number = Column(String, primary_key=True)  # e.g., "001", "002", "003"
    description = Column(String)
    qty = Column(Integer)
    unit_price = Column(Float)
    
    # Relationship back to PO
    purchase_order = relationship("PurchaseOrder", back_populates="line_items")


class GoodsReceipt(Base):
    """
    Multi-line Goods Receipt.
    Each GR can have multiple line items received against a PO.
    """
    __tablename__ = "goods_receipts"

    gr_id = Column(String, primary_key=True)
    po_number = Column(String)  # Reference to PO
    gr_date = Column(String)     # Optional: GR date
    
    # Relationship to line items
    line_items = relationship("GRLineItem", back_populates="goods_receipt", cascade="all, delete-orphan")


class GRLineItem(Base):
    """
    Line item within a Goods Receipt.
    Composite key: gr_id + item_number
    """
    __tablename__ = "gr_line_items"

    gr_id = Column(String, ForeignKey("goods_receipts.gr_id"), primary_key=True)
    po_number = Column(String)  # Reference to PO (for matching)
    item_number = Column(String, primary_key=True)  # Must match PO item_number
    description = Column(String)
    received_qty = Column(Integer)
    
    # Relationship back to GR
    goods_receipt = relationship("GoodsReceipt", back_populates="line_items")


class InvoiceStaging(Base):
    """
    Multi-line Invoice in staging area.
    Each invoice can have multiple line items.
    Once approved, moves to InvoiceFinal.
    """
    __tablename__ = "invoice_staging"

    invoice_id = Column(String, primary_key=True)
    po_number = Column(String)
    vendor_id = Column(String)
    invoice_date = Column(String)
    status = Column(String)  # PENDING, APPROVED, REJECTED, HOLD
    
    # Relationship to line items
    line_items = relationship("InvoiceLineItemStaging", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItemStaging(Base):
    """
    Line item within an invoice in staging.
    Composite key: invoice_id + item_number
    """
    __tablename__ = "invoice_line_items_staging"

    invoice_id = Column(String, ForeignKey("invoice_staging.invoice_id"), primary_key=True)
    item_number = Column(String, primary_key=True)  # Must match PO item_number
    po_number = Column(String)  # Denormalized for quick lookup
    description = Column(String)
    qty = Column(Integer)
    unit_price = Column(Float)
    total_amount = Column(Float)
    
    # Relationship back to invoice
    invoice = relationship("InvoiceStaging", back_populates="line_items")


class InvoiceFinal(Base):
    """
    Multi-line Invoice in final approved state.
    Once approved, invoice moves from staging to final with all line items.
    """
    __tablename__ = "invoice_final"

    invoice_id = Column(String, primary_key=True)
    po_number = Column(String)
    vendor_id = Column(String)
    invoice_date = Column(String)
    approval_status = Column(String)
    
    # Relationship to line items
    line_items = relationship("InvoiceLineItemFinal", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItemFinal(Base):
    """
    Line item within an approved invoice.
    Composite key: invoice_id + item_number
    """
    __tablename__ = "invoice_line_items_final"

    invoice_id = Column(String, ForeignKey("invoice_final.invoice_id"), primary_key=True)
    item_number = Column(String, primary_key=True)
    po_number = Column(String)
    description = Column(String)
    qty = Column(Integer)
    unit_price = Column(Float)
    total_amount = Column(Float)
    match_status = Column(String)  # APPROVED, HOLD, REJECTED
    
    # Relationship back to invoice
    invoice = relationship("InvoiceFinal", back_populates="line_items")
