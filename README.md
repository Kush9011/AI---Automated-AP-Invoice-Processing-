# AI---Automated-AP-Invoice-Processing-
AI-powered Accounts Payable 3-way matching system using FastAPI, Streamlit, SQL, and OpenAI OCR
# Architecture & Data Flow Diagrams

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Streamlit)                         │
│  app.py - Upload → Display → Match → Approve UI                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP Requests
                               ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                               │
│                          main.py                                     │
│                                                                       │
│  POST /upload      → clear staging → extract → insert               │
│  POST /match/{id}  → run 3-way match                               │
│  POST /approve     → move to final                                 │
│  GET /invoice/{id} → retrieve data                                 │
└──────────────────┬───────────────────────────────┬──────────────────┘
                   │                               │
        ┌──────────↓──────────┐        ┌──────────↓──────────┐
        │ Text Extraction     │        │ AI Extraction       │
        │ (extractor.py)      │        │ (ai_service.py)     │
        │ - PDF to text       │        │ - GPT-4 parsing     │
        │ - PyMuPDF (fitz)    │        │ - Multi-line JSON   │
        └─────────────────────┘        └─────────────────────┘
                                               │
        ┌──────────────────────────────────────↓───────────────────┐
        │         Database Operations (db_service.py)              │
        │                                                           │
        │  ┌─────────────────────────────────────────────────┐    │
        │  │ clear_invoice_staging()                         │    │
        │  │ insert_staging(invoice_dict)                    │    │
        │  │ get_po_with_items()                             │    │
        │  │ get_gr_by_po()                                  │    │
        │  │ move_invoice_to_final()                         │    │
        │  └─────────────────────────────────────────────────┘    │
        └────────────────────┬─────────────────────────────────────┘
                             │
        ┌────────────────────↓──────────────────┐
        │    3-Way Match Engine (match_engine.py)│
        │                                        │
        │  For each line item:                  │
        │  1. Get PO line item                  │
        │  2. Get GR line item                  │
        │  3. Run 5 checks:                     │
        │     - PO exists                       │
        │     - GR exists                       │
        │     - Qty match                       │
        │     - Unit price match                │
        │     - Total amount match              │
        │  4. Aggregate results                 │
        └────────────────────┬──────────────────┘
                             │
        ┌────────────────────↓──────────────────┐
        │     SQLAlchemy ORM (models.py)        │
        │                                        │
        │  - 8 database tables                  │
        │  - Relationships & cascades           │
        │  - Composite primary keys             │
        └────────────────────┬──────────────────┘
                             │
                    ↓────────────────↓
              ┌──────────────┐  ┌────────────────┐
              │  SQLite DB   │  │   PostgreSQL   │
              │  (ap.db)     │  │  (production)  │
              └──────────────┘  └────────────────┘
```

---

## 📊 Entity Relationship Diagram (Multi-Line)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│                   PURCHASE ORDERS                                │
│                                                                   │
│  ┌──────────────────────────────┐                               │
│  │  PurchaseOrder               │                               │
│  ├──────────────────────────────┤                               │
│  │ + po_number (PK)             │◄─────────────────┐            │
│  │ + vendor_id                  │                  │ 1:N        │
│  │ + po_date                    │                  │            │
│  └──────────────────────────────┘                  │            │
│                                                    │            │
│                                          ┌─────────┴───────┐    │
│                                          │  POLineItem     │    │
│                                          ├─────────────────┤    │
│                                          │ + po_number(FK) │    │
│                                          │ + item_number   │    │
│                                          │ + description   │    │
│                                          │ + qty           │    │
│                                          │ + unit_price    │    │
│                                          └─────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│                   GOODS RECEIPTS                                 │
│                                                                   │
│  ┌──────────────────────────────┐                               │
│  │  GoodsReceipt                │                               │
│  ├──────────────────────────────┤                               │
│  │ + gr_id (PK)                 │◄─────────────────┐            │
│  │ + po_number                  │                  │ 1:N        │
│  │ + gr_date                    │                  │            │
│  └──────────────────────────────┘                  │            │
│                                                    │            │
│                                          ┌─────────┴───────┐    │
│                                          │  GRLineItem     │    │
│                                          ├─────────────────┤    │
│                                          │ + gr_id (FK)    │    │
│                                          │ + item_number   │    │
│                                          │ + po_number     │    │
│                                          │ + description   │    │
│                                          │ + received_qty  │    │
│                                          └─────────────────┘    │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│                   INVOICE STAGING                                │
│                                                                   │
│  ┌──────────────────────────────────┐                           │
│  │  InvoiceStaging                  │                           │
│  ├──────────────────────────────────┤                           │
│  │ + invoice_id (PK)                │◄──────────────┐           │
│  │ + po_number                      │               │ 1:N      │
│  │ + vendor_id                      │               │           │
│  │ + invoice_date                   │               │           │
│  │ + status                         │               │           │
│  └──────────────────────────────────┘               │           │
│                                           ┌─────────┴────────┐  │
│                                           │InvoiceLineItemSTG│  │
│                                           ├─────────────────┤  │
│                                           │+invoice_id (FK) │  │
│                                           │+item_number     │  │
│                                           │+po_number       │  │
│                                           │+description     │  │
│                                           │+qty             │  │
│                                           │+unit_price      │  │
│                                           │+total_amount    │  │
│                                           └─────────────────┘  │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│                   INVOICE FINAL                                  │
│                                                                   │
│  (Same structure as InvoiceStaging, but for approved invoices)   │
│                                                                   │
│  InvoiceFinal (1) ◄─────────1:N─────► InvoiceLineItemFinal      │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: Upload & Match

```
USER UPLOADS INVOICE PDF
        ↓
   ┌────────────────────────────────────┐
   │ POST /upload (main.py)              │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ clear_invoice_staging()             │
   │ → DELETE all staging rows           │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ extract_text(pdf_bytes)             │
   │ → PyMuPDF reads PDF                 │
   │ → Returns: raw text from pages      │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ extract_invoice(text)               │
   │ → GPT-4 parses text                 │
   │ → Returns: structured JSON          │
   │   {                                 │
   │     invoice_id, po_number, ...      │
   │     line_items: [                   │
   │       {item_number, qty, price...} │
   │     ]                               │
   │   }                                 │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ insert_staging(invoice_dict)        │
   │ → Create InvoiceStaging row         │
   │ → Create N InvoiceLineItemStaging   │
   │   rows (one per line item)          │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ RESPONSE TO CLIENT                  │
   │ {                                   │
   │   invoice_id, line_items_count,     │
   │   extracted_data                    │
   │ }                                   │
   └────────────────────────────────────┘
        ↓
USER SEES EXTRACTED INVOICE & LINE ITEMS
        ↓
USER CLICKS "RUN MATCH"
        ↓
   ┌────────────────────────────────────┐
   │ POST /match/{invoice_id}            │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ run_match(invoice_id)               │
   │ (match_engine.py)                   │
   │                                     │
   │ 1. Get invoice from staging         │
   │ 2. Get all invoice line items       │
   │ 3. Get PO with line items           │
   │ 4. Get GR with line items           │
   │                                     │
   └────────────┬───────────────────────┘
                ↓
    ┌──────────────────────────────────┐
    │ FOR EACH INVOICE LINE ITEM:      │
    │                                  │
    │ Get corresponding PO line item   │
    │ Get corresponding GR line item   │
    │ (by item_number)                 │
    │                                  │
    │ RUN 5 CHECKS:                    │
    │ 1. PO exists?                    │
    │ 2. GR exists?                    │
    │ 3. Qty: INV qty == GR qty?       │
    │ 4. Price: INV price == PO price? │
    │ 5. Total: INV total ==           │
    │    (INV qty × PO price)?          │
    │                                  │
    │ Status: PASS or FAIL             │
    └──────────────┬───────────────────┘
                   ↓
    ┌──────────────────────────────────┐
    │ AGGREGATE RESULTS                │
    │                                  │
    │ Overall Status:                  │
    │   APPROVED (all pass)            │
    │   REJECTED (any fail)            │
    │                                  │
    │ Summary: total/passed/failed     │
    │ Details: per-line results        │
    └──────────────┬───────────────────┘
                   ↓
    ┌──────────────────────────────────┐
    │ RESPONSE TO CLIENT               │
    │ {                                │
    │   status: APPROVED|REJECTED,     │
    │   summary: {...},                │
    │   line_items: [...]              │
    │ }                                │
    └──────────────────────────────────┘
        ↓
USER SEES MATCH RESULTS
        ↓
IF APPROVED: USER CLICKS "APPROVE"
        ↓
   ┌────────────────────────────────────┐
   │ POST /approve/{invoice_id}          │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ move_invoice_to_final(...)          │
   │                                     │
   │ 1. Get invoice from staging         │
   │ 2. Create InvoiceFinal row          │
   │ 3. Create N InvoiceLineItemFinal    │
   │    rows (with match status)         │
   │ 4. Delete from staging              │
   │                                     │
   └────────────┬───────────────────────┘
                ↓
   ┌────────────────────────────────────┐
   │ RESPONSE TO CLIENT                  │
   │ {                                   │
   │   success: true,                    │
   │   message: "Invoice moved..."       │
   │ }                                   │
   └────────────────────────────────────┘
        ↓
USER SEES SUCCESS MESSAGE
```

---

## 🗄️ Database State Timeline

```
STEP 1: UPLOAD
┌──────────────────────────────────────────────────────┐
│ Before:                                              │
│  invoice_staging: empty                              │
│  invoice_line_items_staging: empty                   │
│                                                      │
│ clear_invoice_staging()                              │
│  (no-op since already empty)                         │
│                                                      │
│ extract_invoice() returns:                           │
│  {                                                   │
│    invoice_id: "INV-123",                            │
│    line_items: [                                     │
│      {item_number: "001", qty: 10, ...},             │
│      {item_number: "002", qty: 5, ...},              │
│      {item_number: "003", qty: 20, ...}              │
│    ]                                                 │
│  }                                                   │
│                                                      │
│ insert_staging() executes:                           │
│  INSERT INTO invoice_staging (INV-123, PO-1001...)   │
│  INSERT INTO invoice_line_items_staging (INV-123, 001...) │
│  INSERT INTO invoice_line_items_staging (INV-123, 002...) │
│  INSERT INTO invoice_line_items_staging (INV-123, 003...) │
│                                                      │
│ After:                                               │
│  invoice_staging: 1 row (INV-123)                    │
│  invoice_line_items_staging: 3 rows (001,002,003)    │
└──────────────────────────────────────────────────────┘

STEP 2: MATCH
┌──────────────────────────────────────────────────────┐
│ SELECT from:                                         │
│  invoice_staging WHERE id = INV-123 ✓ (1 row)       │
│  invoice_line_items_staging WHERE id = INV-123       │
│    ✓ (3 rows)                                        │
│  po_line_items WHERE po_number = PO-1001            │
│    ✓ (3 rows)                                        │
│  gr_line_items WHERE gr_id = GR-1001                │
│    ✓ (3 rows)                                        │
│                                                      │
│ Run checks on each triplet:                          │
│  (INV line 001, PO line 001, GR line 001) → PASS     │
│  (INV line 002, PO line 002, GR line 002) → PASS     │
│  (INV line 003, PO line 003, GR line 003) → PASS     │
│                                                      │
│ Update status (optional):                            │
│  UPDATE invoice_staging SET status = 'PENDING'       │
│                                                      │
│ Database unchanged (select only)                     │
└──────────────────────────────────────────────────────┘

STEP 3: APPROVE
┌──────────────────────────────────────────────────────┐
│ Before:                                              │
│  invoice_staging: 1 row (INV-123)                    │
│  invoice_line_items_staging: 3 rows                  │
│  invoice_final: empty                                │
│  invoice_line_items_final: empty                     │
│                                                      │
│ move_invoice_to_final() executes:                    │
│  INSERT INTO invoice_final (INV-123, PO-1001...)     │
│  INSERT INTO invoice_line_items_final (INV-123,001..) │
│  INSERT INTO invoice_line_items_final (INV-123,002..) │
│  INSERT INTO invoice_line_items_final (INV-123,003..) │
│  DELETE FROM invoice_line_items_staging              │
│  DELETE FROM invoice_staging                         │
│                                                      │
│ After:                                               │
│  invoice_staging: empty                              │
│  invoice_line_items_staging: empty                   │
│  invoice_final: 1 row (INV-123) ✓                    │
│  invoice_line_items_final: 3 rows (001,002,003) ✓    │
└──────────────────────────────────────────────────────┘
```

---

## 🔍 Match Engine Logic Flow (Per Line Item)

```
Input: Invoice Line Item (INV-123, 001, qty=10, price=100)
       PO (PO-1001)
       GR (GR-1001)

┌─────────────────────────────────────────────┐
│ Step 1: Get PO line item                    │
│ Query: POLineItem WHERE                     │
│   po_number='PO-1001' AND item_number='001' │
│ Result: PO line 001 FOUND ✓                 │
│                                             │
│ Check 1: PO Line Item Exists                │
│ Result: PASS ✓                              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Step 2: Get GR line item                    │
│ Query: GRLineItem WHERE                     │
│   gr_id='GR-1001' AND item_number='001'     │
│ Result: GR line 001 FOUND ✓                 │
│                                             │
│ Check 2: GR Line Item Exists                │
│ Result: PASS ✓                              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Step 3: Quantity Check                      │
│ Invoice qty: 10                             │
│ GR qty: 10                                  │
│ Compare: 10 == 10 ✓                         │
│                                             │
│ Check 3: Quantity Match                     │
│ Result: PASS ✓                              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Step 4: Unit Price Check                    │
│ Invoice price: 100.0                        │
│ PO price: 100.0                             │
│ Compare: 100.0 == 100.0 ✓                   │
│                                             │
│ Check 4: Unit Price Match                   │
│ Result: PASS ✓                              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Step 5: Total Amount Check                  │
│ Invoice total: 1000.0                       │
│ Expected: 10 × 100.0 = 1000.0               │
│ Compare: 1000.0 == 1000.0 ✓                 │
│                                             │
│ Check 5: Total Amount Match                 │
│ Result: PASS ✓                              │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Line Item Result: PASS                      │
│                                             │
│ All 5 checks passed ✓                       │
└─────────────────────────────────────────────┘

Output: {
  item_number: "001",
  status: "PASS",
  checks: [
    {check_name: "PO Line Item Exists", result: "PASS"},
    {check_name: "GR Line Item Exists", result: "PASS"},
    {check_name: "Quantity Match", result: "PASS"},
    {check_name: "Unit Price Match", result: "PASS"},
    {check_name: "Total Amount Match", result: "PASS"}
  ]
}
```

---

## 🚀 API Request/Response Examples

### Example 1: Upload Multi-Line Invoice

```
REQUEST:
POST /upload HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data

[binary PDF data]

RESPONSE (200 OK):
{
  "success": true,
  "invoice_id": "INV-20240115-001",
  "line_items_count": 3,
  "data": {
    "invoice_id": "INV-20240115-001",
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
      },
      {
        "item_number": "003",
        "description": "Connector",
        "qty": 20,
        "unit_price": 25.0,
        "total_amount": 500.0
      }
    ]
  }
}
```

### Example 2: Run Match

```
REQUEST:
POST /match/INV-20240115-001 HTTP/1.1
Host: localhost:8000

RESPONSE (200 OK):
{
  "invoice_id": "INV-20240115-001",
  "po_number": "PO-1001",
  "status": "APPROVED",
  "summary": {
    "total_line_items": 3,
    "passed_line_items": 3,
    "failed_line_items": 0
  },
  "po_status": "EXISTS",
  "gr_status": "EXISTS",
  "line_items": [
    {
      "item_number": "001",
      "description": "Widget A",
      "status": "PASS",
      "checks": [
        {
          "check_name": "PO Line Item Exists",
          "result": "PASS"
        },
        {
          "check_name": "GR Line Item Exists",
          "result": "PASS"
        },
        {
          "check_name": "Quantity Match",
          "invoice_value": 10,
          "po_value": 10,
          "gr_value": 10,
          "result": "PASS"
        },
        {
          "check_name": "Unit Price Match",
          "invoice_value": 100.0,
          "po_value": 100.0,
          "result": "PASS"
        },
        {
          "check_name": "Total Amount Match",
          "invoice_value": 1000.0,
          "po_value": 1000.0,
          "result": "PASS"
        }
      ]
    },
    // ... items 002 and 003 follow same pattern
  ]
}
```

---

## 📋 Summary Table

| Component | Purpose | Files |
|-----------|---------|-------|
| **Frontend** | User uploads, views, matches | app.py |
| **API Layer** | HTTP endpoints | main.py |
| **Extraction** | PDF → Text → JSON | extractor.py, ai_service.py |
| **Database** | Persistent storage | models.py, db.py |
| **Operations** | CRUD for all objects | db_service.py |
| **Matching** | 3-way line-by-line match | match_engine.py |

---

Last Updated: 2024-01-15
