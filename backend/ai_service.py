import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _extract_json(text: str):
    """
    Safely extracts JSON from model response.
    Handles cases where GPT adds extra text.
    """
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Invalid JSON response:\n{text}")


def extract_invoice(text: str):
    """
    Extract multi-line invoice data from raw text.
    
    Returns:
    {
        "invoice_id": "INV-123",
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

    if not text or not isinstance(text, str):
        raise ValueError("Input text is empty or invalid")

    prompt = f"""
You are an invoice extraction engine. Extract ALL line items from the invoice.

STRICT RULES:
- Return ONLY valid JSON
- No explanation, no markdown, no extra text
- Extract ALL line items, not just one
- Each line item MUST have an item_number
- For each line item, calculate total_amount = qty × unit_price

OUTPUT FORMAT (multi-line):
{{
  "invoice_id": "INV-123",
  "po_number": "PO-1001",
  "vendor_id": "VENDOR-001",
  "invoice_date": "2024-01-15",
  "line_items": [
    {{
      "item_number": "001",
      "description": "Widget A",
      "qty": 10,
      "unit_price": 100.0,
      "total_amount": 1000.0
    }},
    {{
      "item_number": "002",
      "description": "Widget B",
      "qty": 5,
      "unit_price": 50.0,
      "total_amount": 250.0
    }}
  ]
}}

IMPORTANT:
- Do NOT assume single line items
- If invoice has multiple items, extract ALL of them
- item_number should be sequential (001, 002, 003...) if not explicitly provided
- If no item_number is in the source, generate sequential numbers

INPUT:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Return only valid JSON. Extract ALL line items from invoices."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    extracted_data = _extract_json(content)
    
    # Validate structure
    if "line_items" not in extracted_data:
        raise ValueError("Response missing 'line_items' field")
    
    if not isinstance(extracted_data["line_items"], list):
        raise ValueError("'line_items' must be a list")
    
    if len(extracted_data["line_items"]) == 0:
        raise ValueError("No line items extracted from invoice")
    
    # Ensure each line item has required fields
    for idx, line in enumerate(extracted_data["line_items"]):
        if "item_number" not in line:
            line["item_number"] = f"{idx+1:03d}"  # Generate: 001, 002, 003...
        
        if "total_amount" not in line:
            line["total_amount"] = line.get("qty", 0) * line.get("unit_price", 0)
    
    return extracted_data


def extract_invoice_with_retry(text: str, max_retries: int = 2):
    """
    Extract invoice with retry logic for robustness.
    Attempts to extract, retries once if it fails.
    """
    for attempt in range(max_retries):
        try:
            result = extract_invoice(text)
            print(f"✅ Invoice extracted successfully ({len(result['line_items'])} line items)")
            return result
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            # Retry with slightly different prompt on second attempt
    
    raise ValueError("Failed to extract invoice after retries")
