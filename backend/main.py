from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from backend.extractor import extract_text
from backend.ai_service import extract_invoice, extract_invoice_with_retry
from backend.db_service import (
    insert_staging, 
    clear_invoice_staging,
    get_invoice_with_items,
    move_invoice_to_final
)
from backend.match_engine import run_match
from backend.db import SessionLocal
from backend.models import InvoiceStaging


app = FastAPI()


@app.post("/upload")
async def upload(file: UploadFile):
    """
    Upload and process invoice.
    
    Steps:
    1. Clear previous staging data (IMPORTANT!)
    2. Extract text from PDF
    3. Use AI to extract structured data (multi-line support)
    4. Insert into staging database
    
    Returns: Extracted invoice structure with all line items
    """
    try:
        # ============================================================
        # CLEAR STAGING (CRITICAL: Do this before every upload)
        # ============================================================
        clear_invoice_staging()
        
        # ============================================================
        # EXTRACT TEXT FROM PDF
        # ============================================================
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file")
        
        text = extract_text(file_bytes)
        
        if not text or len(text.strip()) == 0:
            raise HTTPException(
                status_code=400, 
                detail="Could not extract text from PDF"
            )
        
        # ============================================================
        # EXTRACT INVOICE USING AI (Multi-line aware)
        # ============================================================
        try:
            ai_output = extract_invoice_with_retry(text, max_retries=2)
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to extract invoice data: {str(e)}"
            )
        
        # ============================================================
        # INSERT INTO STAGING
        # ============================================================
        try:
            invoice_id = insert_staging(ai_output)
            
            # Add invoice_id to response if it was generated
            ai_output["invoice_id"] = invoice_id
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "invoice_id": invoice_id,
                    "line_items_count": len(ai_output.get("line_items", [])),
                    "data": ai_output
                }
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database insertion failed: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/match/{invoice_id}")
def match(invoice_id: str):
    """
    Execute 3-way match for invoice.
    
    Performs line-by-line matching against PO and GR:
    - Checks PO line item exists
    - Checks GR line item exists
    - Matches quantities, unit prices, and totals
    
    Returns: Detailed match report with per-line-item analysis
    """
    try:
        # Run multi-line match
        match_result = run_match(invoice_id)
        
        if match_result.get("status") == "ERROR":
            raise HTTPException(
                status_code=404,
                detail=match_result.get("error", "Unknown error during matching")
            )
        
        return JSONResponse(
            status_code=200,
            content=match_result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Match error: {str(e)}"
        )


@app.post("/approve/{invoice_id}")
def approve(invoice_id: str):
    """
    Approve and move invoice from staging to final.
    
    Only call after successful match.
    Moves invoice and all line items to final table.
    """
    db = SessionLocal()
    try:
        # Get the match result first
        match_result = run_match(invoice_id)
        
        if match_result.get("status") != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve invoice with status: {match_result.get('status')}"
            )
        
        # Move to final
        move_invoice_to_final(db, invoice_id, match_result)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "invoice_id": invoice_id,
                "message": "Invoice moved to final and approved",
                "match_result": match_result
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Approval error: {str(e)}"
        )
    finally:
        db.close()


@app.get("/invoice/{invoice_id}")
def get_invoice(invoice_id: str):
    """
    Retrieve invoice from staging with all line items.
    """
    db = SessionLocal()
    try:
        invoice = get_invoice_with_items(db, invoice_id)
        
        if not invoice:
            raise HTTPException(
                status_code=404,
                detail=f"Invoice {invoice_id} not found"
            )
        
        # Convert to dict with line items
        invoice_dict = {
            "invoice_id": invoice.invoice_id,
            "po_number": invoice.po_number,
            "vendor_id": invoice.vendor_id,
            "invoice_date": invoice.invoice_date,
            "status": invoice.status,
            "line_items": [
                {
                    "item_number": item.item_number,
                    "description": item.description,
                    "qty": item.qty,
                    "unit_price": item.unit_price,
                    "total_amount": item.total_amount
                }
                for item in invoice.line_items
            ]
        }
        
        return JSONResponse(status_code=200, content=invoice_dict)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
