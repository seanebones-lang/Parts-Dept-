from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from loguru import logger
import uuid

from backend.config import settings


class InvoiceGenerator:
    def __init__(self):
        self.storage_path = Path(settings.invoice_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def generate_invoice_number(self) -> str:
        timestamp = datetime.now().strftime('%Y%m%d')
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"INV-{timestamp}-{unique_id}"
    
    def create_invoice(self, invoice_data: Dict[str, Any]) -> str:
        invoice_number = invoice_data.get('invoice_number') or self.generate_invoice_number()
        
        filename = f"invoice_{invoice_number}.pdf"
        filepath = self.storage_path / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("PARTS DEPARTMENT", title_style))
        story.append(Paragraph("Auto Dealer Invoice", styles['Heading2']))
        story.append(Spacer(1, 0.3 * inch))
        
        company_info = [
            ["Parts Department"],
            [invoice_data.get('location_address', 'Multiple Locations')],
            [f"Phone: {invoice_data.get('location_phone', 'N/A')}"],
            [f"Email: {invoice_data.get('location_email', 'parts@dealer.com')}"]
        ]
        
        company_table = Table(company_info, colWidths=[6 * inch])
        company_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(company_table)
        story.append(Spacer(1, 0.3 * inch))
        
        invoice_info = [
            ["Invoice Number:", invoice_number],
            ["Date:", invoice_data.get('date', datetime.now().strftime('%Y-%m-%d'))],
            ["Customer:", invoice_data.get('customer_name', 'N/A')],
            ["Email:", invoice_data.get('customer_email', 'N/A')],
            ["Order ID:", invoice_data.get('order_id', 'N/A')]
        ]
        
        info_table = Table(invoice_info, colWidths=[2 * inch, 4 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.5 * inch))
        
        items = invoice_data.get('items', [])
        
        table_data = [['Item', 'SKU', 'Qty', 'Unit Price', 'Total']]
        
        subtotal = 0
        for item in items:
            name = item.get('name', 'Unknown Part')
            sku = item.get('sku', 'N/A')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0.0)
            total = quantity * price
            subtotal += total
            
            table_data.append([
                name,
                sku,
                str(quantity),
                f"${price:.2f}",
                f"${total:.2f}"
            ])
        
        tax_rate = invoice_data.get('tax_rate', 0.0)
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        table_data.append(['', '', '', 'Subtotal:', f"${subtotal:.2f}"])
        table_data.append(['', '', '', f'Tax ({tax_rate*100:.1f}%):', f"${tax_amount:.2f}"])
        table_data.append(['', '', '', 'TOTAL:', f"${total:.2f}"])
        
        items_table = Table(table_data, colWidths=[2.5 * inch, 1.5 * inch, 0.7 * inch, 1 * inch, 1 * inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
            ('GRID', (0, 0), (-1, -4), 1, colors.black),
            ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 0.5 * inch))
        
        notes = invoice_data.get('notes', '')
        if notes:
            story.append(Paragraph(f"<b>Notes:</b> {notes}", styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        story.append(Paragraph("Thank you for your business!", styles['Normal']))
        story.append(Paragraph("Payment due within 30 days.", styles['Normal']))
        
        doc.build(story)
        
        logger.info(f"Invoice generated: {filepath}")
        
        return str(filepath)
    
    def create_order_invoice(self, order: Dict[str, Any]) -> str:
        invoice_data = {
            'order_id': order.get('id'),
            'customer_name': order.get('customer_name'),
            'customer_email': order.get('customer_email'),
            'items': order.get('items', []),
            'tax_rate': order.get('tax_rate', 0.08),
            'location_address': order.get('location_address'),
            'location_phone': order.get('location_phone'),
            'location_email': order.get('location_email'),
            'notes': order.get('notes', '')
        }
        
        return self.create_invoice(invoice_data)


invoice_generator = InvoiceGenerator()

