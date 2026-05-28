from pydantic import BaseModel
from typing import List

class LineItem(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total: float

class InvoiceData(BaseModel):
    vendor_name: str
    invoice_number: str
    date: str
    total_amount: float
    currency: str
    line_items: List[LineItem]