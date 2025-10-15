from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Location(BaseModel):
    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    manager: Optional[str] = None


class Department(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None


class Part(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    list_price: float
    cost: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None


class Supplier(BaseModel):
    id: str
    name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lead_time_days: Optional[int] = None


class InventoryItem(BaseModel):
    location_id: str
    part_sku: str
    quantity: int
    min_stock: int = 0
    max_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

