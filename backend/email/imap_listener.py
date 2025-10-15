import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from loguru import logger
import asyncio
from datetime import datetime

from backend.config import settings


class IMAPListener:
    def __init__(self):
        self.host = settings.imap_host
        self.port = settings.imap_port
        self.user = settings.imap_user
        self.password = settings.imap_password
        self.connection = None
    
    def connect(self):
        try:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(self.user, self.password)
            logger.info(f"Connected to IMAP server: {self.host}")
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            raise
    
    def disconnect(self):
        if self.connection:
            try:
                self.connection.logout()
                logger.info("Disconnected from IMAP server")
            except:
                pass
    
    def decode_mime_words(self, s):
        if s is None:
            return ""
        decoded_fragments = decode_header(s)
        fragments = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    try:
                        fragments.append(fragment.decode(encoding))
                    except:
                        fragments.append(fragment.decode('utf-8', errors='ignore'))
                else:
                    fragments.append(fragment.decode('utf-8', errors='ignore'))
            else:
                fragments.append(fragment)
        return ''.join(fragments)
    
    def extract_body(self, msg) -> str:
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        return body.strip()
    
    def fetch_unread_emails(self, folder: str = "INBOX", limit: int = None) -> List[Dict[str, Any]]:
        if not self.connection:
            self.connect()
        
        try:
            self.connection.select(folder)
            
            status, messages = self.connection.search(None, 'UNSEEN')
            
            if status != 'OK':
                logger.warning("No unread messages found")
                return []
            
            email_ids = messages[0].split()
            
            if limit:
                email_ids = email_ids[:limit]
            
            emails = []
            
            for email_id in email_ids:
                try:
                    status, msg_data = self.connection.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = self.decode_mime_words(msg.get("Subject", ""))
                    from_addr = self.decode_mime_words(msg.get("From", ""))
                    to_addr = self.decode_mime_words(msg.get("To", ""))
                    date_str = msg.get("Date", "")
                    
                    body = self.extract_body(msg)
                    
                    email_data = {
                        "id": email_id.decode(),
                        "subject": subject,
                        "from": from_addr,
                        "to": to_addr,
                        "date": date_str,
                        "body": body,
                        "raw": raw_email
                    }
                    
                    emails.append(email_data)
                    logger.info(f"Fetched email: {subject[:50]}")
                
                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
            
            return emails
        
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []
    
    def mark_as_read(self, email_id: str):
        if not self.connection:
            return
        
        try:
            self.connection.store(email_id, '+FLAGS', '\\Seen')
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
    
    def move_to_folder(self, email_id: str, destination_folder: str):
        if not self.connection:
            return
        
        try:
            self.connection.copy(email_id, destination_folder)
            self.connection.store(email_id, '+FLAGS', '\\Deleted')
            self.connection.expunge()
            logger.info(f"Moved email {email_id} to {destination_folder}")
        except Exception as e:
            logger.error(f"Error moving email: {e}")


imap_listener = IMAPListener()

