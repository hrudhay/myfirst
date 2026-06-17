import os
import json
import base64
import tempfile
from datetime import datetime
from typing import List, Optional

import anthropic
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, create_tables, InventoryItem, Receipt, Sale
from schemas import (
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    ParsedReceiptItem, ReceiptParseResponse, ReceiptConfirmRequest, ReceiptResponse,
    SaleCreate, SaleResponse,
    DashboardStats
)

app = FastAPI(title="Restaurant Inventory System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    create_tables()


# ─── Receipt Endpoints ────────────────────────────────────────────────────────

@app.post("/api/receipts/parse", response_model=ReceiptParseResponse)
async def parse_receipt(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a receipt image/PDF and extract items using Claude Vision."""
    contents = await file.read()

    # Determine media type
    filename = file.filename or "receipt"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    media_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "pdf": "application/pdf",
    }
    media_type = media_type_map.get(ext, "image/jpeg")

    client = anthropic.Anthropic()

    try:
        if media_type == "application/pdf":
            # Use document source type for PDFs
            encoded = base64.standard_b64encode(contents).decode("utf-8")
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": encoded,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Parse this receipt and return a JSON array of items. "
                                "Each item must have: name (string), quantity (number), "
                                "unit (string like 'each', 'kg', 'lb', 'liter', 'box'), "
                                "unit_price (number), total_price (number), "
                                "category (string like 'Produce', 'Meat', 'Dairy', "
                                "'Beverages', 'Dry Goods', 'Other'). "
                                "Return ONLY a valid JSON array, no other text."
                            )
                        }
                    ],
                }]
            )
        else:
            # Image file
            encoded = base64.standard_b64encode(contents).decode("utf-8")
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": encoded,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Parse this receipt and return a JSON array of items. "
                                "Each item must have: name (string), quantity (number), "
                                "unit (string like 'each', 'kg', 'lb', 'liter', 'box'), "
                                "unit_price (number), total_price (number), "
                                "category (string like 'Produce', 'Meat', 'Dairy', "
                                "'Beverages', 'Dry Goods', 'Other'). "
                                "Return ONLY a valid JSON array, no other text."
                            )
                        }
                    ],
                }]
            )

        raw_text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed_items_raw = json.loads(raw_text)
        parsed_items = [ParsedReceiptItem(**item) for item in parsed_items_raw]
        total_amount = sum(item.total_price for item in parsed_items)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not parse JSON from Claude response."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing receipt: {str(e)}"
        )

    # Save receipt record
    receipt = Receipt(
        filename=filename,
        total_amount=total_amount,
        parsed_items=json.dumps([item.model_dump() for item in parsed_items]),
        status="pending",
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)

    return ReceiptParseResponse(
        filename=filename,
        items=parsed_items,
        total_amount=total_amount,
        receipt_id=receipt.id,
    )


@app.post("/api/receipts/confirm")
def confirm_receipt(request: ReceiptConfirmRequest, db: Session = Depends(get_db)):
    """Confirm parsed receipt and update inventory quantities."""
    receipt = db.query(Receipt).filter(Receipt.id == request.receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    for item in request.items:
        # Try to find existing inventory item (case-insensitive)
        existing = db.query(InventoryItem).filter(
            InventoryItem.name.ilike(item.name)
        ).first()

        if existing:
            existing.quantity += item.quantity
            existing.cost_per_unit = item.unit_price
            existing.updated_at = datetime.utcnow()
        else:
            new_item = InventoryItem(
                name=item.name,
                category=item.category,
                quantity=item.quantity,
                unit=item.unit,
                cost_per_unit=item.unit_price,
                low_stock_threshold=10.0,
            )
            db.add(new_item)

    receipt.status = "confirmed"
    receipt.parsed_items = json.dumps([item.model_dump() for item in request.items])
    total = sum(i.total_price for i in request.items)
    receipt.total_amount = total

    db.commit()
    return {"message": "Receipt confirmed and inventory updated", "total_amount": total}


# ─── Inventory Endpoints ──────────────────────────────────────────────────────

@app.get("/api/inventory", response_model=List[InventoryItemResponse])
def list_inventory(db: Session = Depends(get_db)):
    return db.query(InventoryItem).order_by(InventoryItem.name).all()


@app.post("/api/inventory", response_model=InventoryItemResponse, status_code=201)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db)):
    db_item = InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@app.put("/api/inventory/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: int, item: InventoryItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)
    db_item.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_item)
    return db_item


@app.delete("/api/inventory/{item_id}")
def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(db_item)
    db.commit()
    return {"message": "Item deleted"}


# ─── Sales Endpoints ──────────────────────────────────────────────────────────

@app.post("/api/sales", response_model=SaleResponse, status_code=201)
def record_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Record a sale and deduct from inventory."""
    if sale.inventory_item_id:
        db_item = db.query(InventoryItem).filter(
            InventoryItem.id == sale.inventory_item_id
        ).first()
        if not db_item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        if db_item.quantity < sale.quantity_sold:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {db_item.quantity} {db_item.unit}"
            )
        db_item.quantity -= sale.quantity_sold
        db_item.updated_at = datetime.utcnow()

    db_sale = Sale(**sale.model_dump())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


@app.get("/api/sales", response_model=List[SaleResponse])
def list_sales(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Sale).order_by(Sale.sale_date.desc()).limit(limit).all()


# ─── Dashboard Endpoint ───────────────────────────────────────────────────────

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    items = db.query(InventoryItem).all()
    total_items = len(items)
    total_value = sum(i.quantity * i.cost_per_unit for i in items)

    low_stock_items = [
        i for i in items if i.quantity <= i.low_stock_threshold
    ]

    recent_sales = (
        db.query(Sale).order_by(Sale.sale_date.desc()).limit(10).all()
    )
    recent_receipts = (
        db.query(Receipt).order_by(Receipt.upload_date.desc()).limit(5).all()
    )

    return DashboardStats(
        total_items=total_items,
        total_value=round(total_value, 2),
        low_stock_count=len(low_stock_items),
        low_stock_items=low_stock_items,
        recent_sales=recent_sales,
        recent_receipts=recent_receipts,
    )
