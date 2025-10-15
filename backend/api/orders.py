from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.models import Order, OrderItem, Invoice
from backend.invoice.generator import invoice_generator
from backend.email.smtp_sender import smtp_sender
from backend.graph.queries import inventory_queries

router = APIRouter()


class OrderItemCreate(BaseModel):
    part_sku: str
    part_name: str
    quantity: int
    unit_price: float


class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    location_id: str
    items: List[OrderItemCreate]
    notes: Optional[str] = None
    tax_rate: float = 0.08


@router.post("/")
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    try:
        subtotal = sum(item.quantity * item.unit_price for item in order_data.items)
        tax_amount = subtotal * order_data.tax_rate
        total = subtotal + tax_amount
        
        order = Order(
            customer_name=order_data.customer_name,
            customer_email=order_data.customer_email,
            customer_phone=order_data.customer_phone,
            location_id=order_data.location_id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total=total,
            tax_rate=order_data.tax_rate,
            notes=order_data.notes,
            status='pending'
        )
        
        db.add(order)
        await db.flush()
        
        for item_data in order_data.items:
            total_price = item_data.quantity * item_data.unit_price
            order_item = OrderItem(
                order_id=order.id,
                part_sku=item_data.part_sku,
                part_name=item_data.part_name,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=total_price
            )
            db.add(order_item)
        
        await db.commit()
        await db.refresh(order)
        
        return {
            "success": True,
            "order_id": order.id,
            "total": total,
            "status": order.status
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{order_id}")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "id": order.id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "location_id": order.location_id,
            "status": order.status,
            "subtotal": order.subtotal,
            "tax_amount": order.tax_amount,
            "total": order.total,
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "part_sku": item.part_sku,
                    "part_name": item.part_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in order.items
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/invoice")
async def generate_invoice_for_order(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        locations = await inventory_queries.get_all_locations()
        location_info = next((loc for loc in locations if loc['id'] == order.location_id), {})
        
        invoice_data = {
            'order_id': order.id,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'items': [
                {
                    'name': item.part_name,
                    'sku': item.part_sku,
                    'quantity': item.quantity,
                    'price': item.unit_price
                }
                for item in order.items
            ],
            'tax_rate': order.tax_rate,
            'location_address': location_info.get('city', ''),
            'location_phone': location_info.get('phone', ''),
            'location_email': location_info.get('email', ''),
            'notes': order.notes or ''
        }
        
        invoice_path = invoice_generator.create_invoice(invoice_data)
        
        invoice_number = invoice_path.split('_')[-1].replace('.pdf', '')
        
        invoice_record = Invoice(
            invoice_number=invoice_number,
            order_id=order.id,
            file_path=invoice_path,
            sent=False
        )
        
        db.add(invoice_record)
        await db.commit()
        
        return {
            "success": True,
            "invoice_number": invoice_number,
            "invoice_path": invoice_path
        }
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{order_id}/invoice/send")
async def send_invoice_email(order_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(Order).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if not order.invoice:
            raise HTTPException(status_code=404, detail="Invoice not generated yet")
        
        sent = await smtp_sender.send_invoice_email(
            to=order.customer_email,
            customer_name=order.customer_name,
            invoice_path=order.invoice.file_path,
            invoice_number=order.invoice.invoice_number,
            total_amount=order.total
        )
        
        if sent:
            order.invoice.sent = True
            order.invoice.sent_at = datetime.utcnow()
            await db.commit()
        
        return {
            "success": sent,
            "message": "Invoice sent successfully" if sent else "Failed to send invoice"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

