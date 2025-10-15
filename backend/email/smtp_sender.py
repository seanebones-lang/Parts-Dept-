import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict
from loguru import logger
from pathlib import Path

from backend.config import settings


class SMTPSender:
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.from_email = settings.email_from
    
    async def send_email(self, to: str, subject: str, body: str,
                        cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None,
                        attachments: Optional[List[Dict]] = None,
                        html: bool = False) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            if bcc:
                msg['Bcc'] = ', '.join(bcc)
            
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            if attachments:
                for attachment in attachments:
                    file_path = attachment.get('path')
                    file_name = attachment.get('name', Path(file_path).name)
                    
                    with open(file_path, 'rb') as f:
                        attach = MIMEApplication(f.read(), _subtype="pdf")
                        attach.add_header('Content-Disposition', 'attachment', filename=file_name)
                        msg.attach(attach)
            
            recipients = [to]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                start_tls=True
            )
            
            logger.info(f"Email sent successfully to {to}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_invoice_email(self, to: str, customer_name: str, 
                                 invoice_path: str, invoice_number: str,
                                 total_amount: float) -> bool:
        subject = f"Invoice #{invoice_number} - Parts Department"
        
        body = f"""
Dear {customer_name},

Thank you for your order. Please find attached your invoice #{invoice_number}.

Invoice Total: ${total_amount:.2f}

If you have any questions or concerns, please don't hesitate to contact us.

Best regards,
Parts Department Team
        """.strip()
        
        attachments = [{'path': invoice_path, 'name': f'invoice_{invoice_number}.pdf'}]
        
        return await self.send_email(to, subject, body, attachments=attachments)
    
    async def send_order_confirmation(self, to: str, customer_name: str,
                                     order_id: str, items: List[Dict]) -> bool:
        subject = f"Order Confirmation #{order_id}"
        
        items_list = "\n".join([
            f"- {item['name']} (SKU: {item['sku']}) x {item['quantity']} - ${item['price']:.2f}"
            for item in items
        ])
        
        total = sum(item['price'] * item['quantity'] for item in items)
        
        body = f"""
Dear {customer_name},

Your order #{order_id} has been confirmed!

Order Details:
{items_list}

Total: ${total:.2f}

We'll notify you once your order is ready for pickup or has been shipped.

Thank you for your business!

Best regards,
Parts Department Team
        """.strip()
        
        return await self.send_email(to, subject, body)


smtp_sender = SMTPSender()

