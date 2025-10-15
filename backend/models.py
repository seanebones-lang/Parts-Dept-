from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String)
    location_id = Column(String, nullable=False)
    
    status = Column(String, default='pending')
    
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.08)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = 'order_items'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    
    part_sku = Column(String, nullable=False)
    part_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    order = relationship("Order", back_populates="items")


class Invoice(Base):
    __tablename__ = 'invoices'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    invoice_number = Column(String, unique=True, nullable=False)
    order_id = Column(String, ForeignKey('orders.id'), nullable=False)
    
    file_path = Column(String, nullable=False)
    
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="invoice")


class EmailLog(Base):
    __tablename__ = 'email_logs'
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email_id = Column(String)
    
    from_address = Column(String, nullable=False)
    to_address = Column(String, nullable=False)
    subject = Column(String)
    body = Column(Text)
    
    intent = Column(String)
    confidence = Column(Float)
    entities = Column(JSON)
    
    response_generated = Column(Text)
    requires_human = Column(Boolean, default=False)
    
    processed_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    
    status = Column(String, default='pending')

