from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# InventoryItem schemas
class InventoryItemBase(BaseModel):
    name: str
    category: Optional[str] = "Other"
    quantity: Optional[float] = 0.0
    unit: Optional[str] = "each"
    cost_per_unit: Optional[float] = 0.0
    low_stock_threshold: Optional[float] = 10.0


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    cost_per_unit: Optional[float] = None
    low_stock_threshold: Optional[float] = None


class InventoryItemResponse(InventoryItemBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Receipt schemas
class ParsedReceiptItem(BaseModel):
    name: str
    quantity: float
    unit: str
    unit_price: float
    total_price: float
    category: Optional[str] = "Other"


class ReceiptParseResponse(BaseModel):
    filename: str
    items: List[ParsedReceiptItem]
    total_amount: float
    receipt_id: int


class ReceiptConfirmRequest(BaseModel):
    receipt_id: int
    items: List[ParsedReceiptItem]


class ReceiptResponse(BaseModel):
    id: int
    filename: str
    upload_date: datetime
    total_amount: float
    status: str

    class Config:
        from_attributes = True


# Sale schemas
class SaleCreate(BaseModel):
    inventory_item_id: Optional[int] = None
    item_name: str
    quantity_sold: float
    unit: Optional[str] = "each"
    notes: Optional[str] = ""


class SaleResponse(BaseModel):
    id: int
    inventory_item_id: Optional[int] = None
    item_name: str
    quantity_sold: float
    unit: str
    sale_date: datetime
    notes: Optional[str] = ""

    class Config:
        from_attributes = True


# Dashboard schema
class DashboardStats(BaseModel):
    total_items: int
    total_value: float
    low_stock_count: int
    low_stock_items: List[InventoryItemResponse]
    recent_sales: List[SaleResponse]
    recent_receipts: List[ReceiptResponse]
