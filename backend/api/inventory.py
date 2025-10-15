from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from backend.graph.queries import inventory_queries
from backend.graph.schema import Location, Part, Department, Supplier, InventoryItem

router = APIRouter()


class LocationCreate(BaseModel):
    id: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    phone: str
    email: str
    manager: Optional[str] = None


class PartCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    list_price: float
    cost: Optional[float] = None


class InventoryAdd(BaseModel):
    location_id: str
    part_sku: str
    quantity: int
    min_stock: int = 0
    max_stock: Optional[int] = None
    reorder_point: Optional[int] = None


class TransferRequest(BaseModel):
    from_location_id: str
    to_location_id: str
    part_sku: str
    quantity: int


@router.post("/locations")
async def create_location(location: LocationCreate):
    try:
        location_obj = Location(**location.model_dump())
        result = await inventory_queries.create_location(location_obj)
        return {"success": True, "location": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/locations")
async def get_locations():
    try:
        locations = await inventory_queries.get_all_locations()
        return {"locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parts")
async def create_part(part: PartCreate):
    try:
        part_obj = Part(**part.model_dump())
        result = await inventory_queries.create_part(part_obj)
        return {"success": True, "part": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory")
async def add_inventory(inventory: InventoryAdd):
    try:
        inventory_obj = InventoryItem(**inventory.model_dump())
        result = await inventory_queries.add_inventory(inventory_obj)
        return {"success": True, "inventory": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/check/{part_sku}")
async def check_inventory(part_sku: str, location_id: Optional[str] = None):
    try:
        inventory = await inventory_queries.check_inventory(part_sku, location_id)
        return {"inventory": inventory}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inventory/low-stock")
async def get_low_stock(location_id: Optional[str] = None):
    try:
        low_stock = await inventory_queries.get_low_stock_items(location_id)
        return {"low_stock_items": low_stock}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inventory/transfer")
async def transfer_inventory(transfer: TransferRequest):
    try:
        result = await inventory_queries.transfer_inventory(
            transfer.from_location_id,
            transfer.to_location_id,
            transfer.part_sku,
            transfer.quantity
        )
        
        if not result:
            raise HTTPException(status_code=400, detail="Transfer failed - insufficient inventory")
        
        return {"success": True, "transfer": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parts/search")
async def search_parts(q: str, limit: int = 10):
    try:
        parts = await inventory_queries.find_parts_by_name(q, limit)
        return {"parts": parts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

