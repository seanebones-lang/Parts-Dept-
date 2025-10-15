from celery import Task
from backend.workers.celery_app import celery_app
from backend.email.imap_listener import imap_listener
from backend.email.processor import email_processor
from backend.email.smtp_sender import smtp_sender
from backend.graph.queries import inventory_queries
from loguru import logger
import asyncio


class AsyncTask(Task):
    def __call__(self, *args, **kwargs):
        return asyncio.run(self.run_async(*args, **kwargs))


@celery_app.task(name='backend.workers.tasks.process_inbox_task', base=AsyncTask)
async def process_inbox_task(limit: int = 50):
    logger.info("Starting scheduled inbox processing")
    
    try:
        emails = imap_listener.fetch_unread_emails(limit=limit)
        logger.info(f"Fetched {len(emails)} unread emails")
        
        processed_count = 0
        responded_count = 0
        
        for email_data in emails:
            try:
                result = await email_processor.process_email(email_data)
                processed_count += 1
                
                if not result['response_data']['requires_human']:
                    response_text = result['response_data']['response']
                    subject = f"Re: {email_data.get('subject', '')}"
                    
                    sent = await smtp_sender.send_email(
                        to=email_data.get('from', ''),
                        subject=subject,
                        body=response_text
                    )
                    
                    if sent:
                        responded_count += 1
                        imap_listener.mark_as_read(email_data.get('id'))
                        logger.info(f"Auto-responded to email: {email_data.get('subject', '')[:50]}")
                    else:
                        logger.warning(f"Failed to send response for: {email_data.get('subject', '')[:50]}")
                else:
                    logger.info(f"Email requires human attention: {email_data.get('subject', '')[:50]}")
                    imap_listener.move_to_folder(email_data.get('id'), 'NeedsReview')
            
            except Exception as e:
                logger.error(f"Error processing email {email_data.get('id')}: {e}")
        
        imap_listener.disconnect()
        
        logger.info(f"Inbox processing complete: {processed_count} processed, {responded_count} auto-responded")
        
        return {
            'success': True,
            'fetched': len(emails),
            'processed': processed_count,
            'responded': responded_count
        }
    
    except Exception as e:
        logger.error(f"Inbox processing failed: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='backend.workers.tasks.send_email_task', base=AsyncTask)
async def send_email_task(to: str, subject: str, body: str, **kwargs):
    logger.info(f"Sending email to {to}: {subject}")
    
    try:
        success = await smtp_sender.send_email(to, subject, body, **kwargs)
        
        if success:
            logger.info(f"Email sent successfully to {to}")
        else:
            logger.warning(f"Failed to send email to {to}")
        
        return {'success': success, 'to': to}
    
    except Exception as e:
        logger.error(f"Email send task failed: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='backend.workers.tasks.check_low_stock_task', base=AsyncTask)
async def check_low_stock_task():
    logger.info("Checking low stock items across all locations")
    
    try:
        low_stock_items = await inventory_queries.get_low_stock_items()
        
        if not low_stock_items:
            logger.info("No low stock items found")
            return {'success': True, 'low_stock_count': 0}
        
        logger.warning(f"Found {len(low_stock_items)} low stock items")
        
        grouped_by_location = {}
        for item in low_stock_items:
            location = item['location']
            if location not in grouped_by_location:
                grouped_by_location[location] = []
            grouped_by_location[location].append(item)
        
        for location, items in grouped_by_location.items():
            items_list = "\n".join([
                f"- {item['part_name']} (SKU: {item['sku']}): {item['current_quantity']} units (reorder at {item['reorder_point']})"
                for item in items
            ])
            
            subject = f"Low Stock Alert - {location}"
            body = f"""
Low Stock Alert for {location}

The following items are at or below reorder point:

{items_list}

Please review and place orders as needed.

This is an automated message from the Parts Department System.
            """.strip()
            
            logger.info(f"Would send low stock alert for {location} ({len(items)} items)")
        
        return {
            'success': True,
            'low_stock_count': len(low_stock_items),
            'locations_affected': len(grouped_by_location)
        }
    
    except Exception as e:
        logger.error(f"Low stock check failed: {e}")
        return {'success': False, 'error': str(e)}


@celery_app.task(name='backend.workers.tasks.generate_and_send_invoice_task', base=AsyncTask)
async def generate_and_send_invoice_task(order_id: str):
    from backend.invoice.generator import invoice_generator
    from backend.database import AsyncSessionLocal
    from backend.models import Order, Invoice
    from sqlalchemy import select
    from datetime import datetime
    
    logger.info(f"Generating and sending invoice for order {order_id}")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Order).where(Order.id == order_id))
            order = result.scalar_one_or_none()
            
            if not order:
                logger.error(f"Order {order_id} not found")
                return {'success': False, 'error': 'Order not found'}
            
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
            
            sent = await smtp_sender.send_invoice_email(
                to=order.customer_email,
                customer_name=order.customer_name,
                invoice_path=invoice_path,
                invoice_number=invoice_number,
                total_amount=order.total
            )
            
            if sent:
                invoice_record.sent = True
                invoice_record.sent_at = datetime.utcnow()
                await db.commit()
                logger.info(f"Invoice sent successfully for order {order_id}")
            
            return {
                'success': sent,
                'invoice_number': invoice_number,
                'order_id': order_id
            }
    
    except Exception as e:
        logger.error(f"Invoice generation/send failed: {e}")
        return {'success': False, 'error': str(e)}

