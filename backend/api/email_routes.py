from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from backend.database import get_db
from backend.models import EmailLog
from backend.email.imap_listener import imap_listener
from backend.email.processor import email_processor
from backend.email.smtp_sender import smtp_sender

router = APIRouter()


class EmailProcessRequest(BaseModel):
    subject: str
    from_address: str
    body: str


class EmailResponse(BaseModel):
    to: str
    subject: str
    body: str


@router.post("/process")
async def process_email_endpoint(
    email_data: EmailProcessRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        email_dict = {
            'subject': email_data.subject,
            'from': email_data.from_address,
            'body': email_data.body
        }
        
        result = await email_processor.process_email(email_dict)
        
        email_log = EmailLog(
            from_address=email_data.from_address,
            to_address='system',
            subject=email_data.subject,
            body=email_data.body,
            intent=result['classification']['intent'],
            confidence=result['classification']['confidence'],
            entities=result['entities'],
            response_generated=result['response_data'].get('response'),
            requires_human=result['response_data']['requires_human'],
            status='processed'
        )
        
        db.add(email_log)
        await db.commit()
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send")
async def send_email_endpoint(email_data: EmailResponse):
    try:
        success = await smtp_sender.send_email(
            to=email_data.to,
            subject=email_data.subject,
            body=email_data.body
        )
        
        return {
            "success": success,
            "message": "Email sent successfully" if success else "Failed to send email"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fetch")
async def fetch_unread_emails(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    try:
        emails = imap_listener.fetch_unread_emails(limit=limit)
        
        return {
            "count": len(emails),
            "emails": emails
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        imap_listener.disconnect()


@router.post("/process-inbox")
async def process_inbox(
    background_tasks: BackgroundTasks,
    limit: int = 10,
    auto_respond: bool = False,
    db: AsyncSession = Depends(get_db)
):
    try:
        emails = imap_listener.fetch_unread_emails(limit=limit)
        
        processed_count = 0
        results = []
        
        for email_data in emails:
            try:
                result = await email_processor.process_email(email_data)
                
                email_log = EmailLog(
                    email_id=email_data.get('id'),
                    from_address=email_data.get('from', ''),
                    to_address=email_data.get('to', ''),
                    subject=email_data.get('subject', ''),
                    body=email_data.get('body', ''),
                    intent=result['classification']['intent'],
                    confidence=result['classification']['confidence'],
                    entities=result['entities'],
                    response_generated=result['response_data'].get('response'),
                    requires_human=result['response_data']['requires_human'],
                    status='processed'
                )
                
                db.add(email_log)
                
                if auto_respond and not result['response_data']['requires_human']:
                    response_text = result['response_data']['response']
                    subject = f"Re: {email_data.get('subject', '')}"
                    
                    background_tasks.add_task(
                        smtp_sender.send_email,
                        to=email_data.get('from', ''),
                        subject=subject,
                        body=response_text
                    )
                    
                    email_log.responded_at = datetime.utcnow()
                    email_log.status = 'responded'
                
                imap_listener.mark_as_read(email_data.get('id'))
                
                processed_count += 1
                results.append({
                    "email_id": email_data.get('id'),
                    "subject": email_data.get('subject', ''),
                    "intent": result['classification']['intent'],
                    "requires_human": result['response_data']['requires_human']
                })
            
            except Exception as e:
                logger.error(f"Error processing email {email_data.get('id')}: {e}")
                results.append({
                    "email_id": email_data.get('id'),
                    "error": str(e)
                })
        
        await db.commit()
        imap_listener.disconnect()
        
        return {
            "success": True,
            "total_fetched": len(emails),
            "processed": processed_count,
            "results": results
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_email_logs(
    limit: int = 50,
    requires_human: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(EmailLog).order_by(EmailLog.processed_at.desc()).limit(limit)
        
        if requires_human is not None:
            query = query.where(EmailLog.requires_human == requires_human)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return {
            "count": len(logs),
            "logs": [
                {
                    "id": log.id,
                    "from": log.from_address,
                    "subject": log.subject,
                    "intent": log.intent,
                    "confidence": log.confidence,
                    "requires_human": log.requires_human,
                    "status": log.status,
                    "processed_at": log.processed_at.isoformat() if log.processed_at else None
                }
                for log in logs
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

