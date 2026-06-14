from backend.db import SessionLocal
from backend.db_service import (
    get_invoice_with_items,
    get_invoice_line_items,
    get_po_with_items,
    get_po_line_item,
    get_gr_by_po,
    get_gr_line_item,
    update_invoice_status
)


def run_match(invoice_id):
    """
    Execute 3-way match for multi-line invoice.
    
    For each line item in invoice:
    1. Check if PO line item exists (by po_number + item_number)
    2. Check if GR line item exists (by po_number + item_number)
    3. Match quantities and amounts
    
    Returns comprehensive match report with per-line-item analysis.
    """
    db = SessionLocal()
    
    try:
        # ============================================================
        # FETCH INVOICE AND RELATED DOCUMENTS
        # ============================================================
        
        invoice = get_invoice_with_items(db, invoice_id)
        if not invoice:
            return {
                "invoice_id": invoice_id,
                "status": "ERROR",
                "error": f"Invoice {invoice_id} not found"
            }
        
        invoice_line_items = get_invoice_line_items(db, invoice_id)
        
        # Get PO with all line items
        po = get_po_with_items(db, invoice.po_number)
        
        # Get GR for this PO
        gr = get_gr_by_po(db, invoice.po_number)
        
        # ============================================================
        # VALIDATE PO AND GR EXIST
        # ============================================================
        
        po_exists = po is not None
        gr_exists = gr is not None
        
        if not po_exists or not gr_exists:
            return {
                "invoice_id": invoice_id,
                "status": "REJECTED",
                "reason": f"PO exists: {po_exists}, GR exists: {gr_exists}",
                "line_items": []
            }
        
        # ============================================================
        # MATCH EACH LINE ITEM
        # ============================================================
        
        line_item_results = []
        overall_passed = True
        
        for inv_line in invoice_line_items:
            item_number = inv_line.item_number
            
            # Get PO line item
            po_line = get_po_line_item(db, invoice.po_number, item_number)
            
            # Get GR line item
            gr_line = get_gr_line_item(db, gr.gr_id, item_number) if gr else None
            
            # ========================================================
            # INDIVIDUAL LINE ITEM CHECKS
            # ========================================================
            
            checks = []
            line_passed = True
            
            # Check 1: PO Line Item Exists
            po_line_exists = po_line is not None
            check_po_exists = {
                "check_name": "PO Line Item Exists",
                "item_number": item_number,
                "invoice_value": item_number,
                "po_value": po_line.item_number if po_line else None,
                "gr_value": None,
                "result": "PASS" if po_line_exists else "FAIL"
            }
            checks.append(check_po_exists)
            line_passed = line_passed and po_line_exists
            
            # Check 2: GR Line Item Exists
            gr_line_exists = gr_line is not None
            check_gr_exists = {
                "check_name": "GR Line Item Exists",
                "item_number": item_number,
                "invoice_value": item_number,
                "po_value": None,
                "gr_value": gr_line.item_number if gr_line else None,
                "result": "PASS" if gr_line_exists else "FAIL"
            }
            checks.append(check_gr_exists)
            line_passed = line_passed and gr_line_exists
            
            # Check 3: Quantity Match (Invoice Qty = GR Received Qty)
            qty_match = (
                po_line and gr_line and 
                inv_line.qty == gr_line.received_qty
            )
            check_qty = {
                "check_name": "Quantity Match",
                "item_number": item_number,
                "invoice_value": inv_line.qty,
                "po_value": po_line.qty if po_line else None,
                "gr_value": gr_line.received_qty if gr_line else None,
                "result": "PASS" if qty_match else "FAIL"
            }
            checks.append(check_qty)
            line_passed = line_passed and qty_match
            
            # Check 4: Unit Price Match (Invoice Unit Price = PO Unit Price)
            unit_price_match = (
                po_line and 
                inv_line.unit_price == po_line.unit_price
            )
            check_unit_price = {
                "check_name": "Unit Price Match",
                "item_number": item_number,
                "invoice_value": inv_line.unit_price,
                "po_value": po_line.unit_price if po_line else None,
                "gr_value": None,
                "result": "PASS" if unit_price_match else "FAIL"
            }
            checks.append(check_unit_price)
            line_passed = line_passed and unit_price_match
            
            # Check 5: Total Amount Match
            # Invoice Total = Invoice Qty × PO Unit Price
            expected_total = (
                inv_line.qty * po_line.unit_price 
                if po_line else None
            )
            total_match = (
                po_line and 
                inv_line.total_amount == expected_total
            )
            check_total = {
                "check_name": "Total Amount Match",
                "item_number": item_number,
                "invoice_value": inv_line.total_amount,
                "po_value": expected_total,
                "gr_value": None,
                "result": "PASS" if total_match else "FAIL"
            }
            checks.append(check_total)
            line_passed = line_passed and total_match
            
            # ========================================================
            # AGGREGATE LINE ITEM RESULT
            # ========================================================
            
            line_result = {
                "item_number": item_number,
                "description": inv_line.description,
                "status": "PASS" if line_passed else "FAIL",
                "checks": checks
            }
            
            line_item_results.append(line_result)
            overall_passed = overall_passed and line_passed
        
        # ============================================================
        # DETERMINE OVERALL STATUS
        # ============================================================
        
        overall_status = "APPROVED" if overall_passed else "REJECTED"
        
        # Update invoice status
        update_invoice_status(db, invoice_id, "PENDING" if overall_passed else "REJECTED")
        
        # ============================================================
        # RETURN COMPREHENSIVE REPORT
        # ============================================================
        
        return {
            "invoice_id": invoice_id,
            "po_number": invoice.po_number,
            "status": overall_status,
            "summary": {
                "total_line_items": len(invoice_line_items),
                "passed_line_items": sum(
                    1 for item in line_item_results 
                    if item["status"] == "PASS"
                ),
                "failed_line_items": sum(
                    1 for item in line_item_results 
                    if item["status"] == "FAIL"
                )
            },
            "line_items": line_item_results,
            "po_status": "EXISTS" if po_exists else "MISSING",
            "gr_status": "EXISTS" if gr_exists else "MISSING"
        }
        
    except Exception as e:
        return {
            "invoice_id": invoice_id,
            "status": "ERROR",
            "error": str(e)
        }
    finally:
        db.close()


def get_match_summary(match_result):
    """
    Generate a user-friendly summary of match results.
    """
    status = match_result.get("status")
    summary = match_result.get("summary", {})
    
    if status == "ERROR":
        return f"❌ Error: {match_result.get('error')}"
    
    passed = summary.get("passed_line_items", 0)
    total = summary.get("total_line_items", 0)
    
    if status == "APPROVED":
        return f"✅ All {total} line items matched successfully"
    else:
        failed = summary.get("failed_line_items", 0)
        return f"❌ Failed: {failed}/{total} line items. Passed: {passed}/{total}"
