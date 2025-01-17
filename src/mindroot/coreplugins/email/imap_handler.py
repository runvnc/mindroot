import imaplib
import email
import chardet
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class IMAPHandler:
    def __init__(self, config: Dict):
        self.imap_server = config.get('imap_server')
        self.imap_port = config.get('imap_port', 993)
        self.email = config['email']
        self.password = config['password']
        self.default_batch_size = config.get('batch_size', 50)
        self.default_max_messages = config.get('max_messages', 100)

    def connect(self) -> imaplib.IMAP4:
        """Establish IMAP connection"""
        try:
            server = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            server.login(self.email, self.password)
            return server
        except Exception as e:
            logger.error(f"IMAP Connection error: {str(e)}")
            raise

    def build_search_criteria(self, criteria: Dict = None, last_uid: str = None) -> str:
        """Build IMAP search criteria string"""
        search_terms = []
        
        # Add UID range if we're paginating
        if last_uid:
            search_terms.append(f'UID 1:{last_uid}')
        
        if criteria:
            if criteria.get('unread_only'):
                search_terms.append('UNSEEN')
            if criteria.get('since_date'):
                date_str = criteria['since_date'].strftime("%d-%b-%Y")
                search_terms.append(f'SINCE "{date_str}"')
            if criteria.get('from'):
                search_terms.append(f'FROM "{criteria["from"]}"')
            if criteria.get('subject'):
                search_terms.append(f'SUBJECT "{criteria["subject"]}"')
        else:
            # Default to messages from the last 30 days
            thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
            search_terms.append(f'SINCE "{thirty_days_ago}"')

        return ' '.join(search_terms) if search_terms else 'ALL'

    def decode_text(self, text_bytes: bytes) -> str:
        """Safely decode text bytes to string, trying multiple encodings"""
        if not text_bytes:
            return ""
            
        # Try UTF-8 first
        try:
            return text_bytes.decode('utf-8')
        except UnicodeDecodeError:
            pass

        # Try to detect encoding
        try:
            detected = chardet.detect(text_bytes)
            if detected and detected['encoding']:
                return text_bytes.decode(detected['encoding'])
        except Exception:
            pass

        # Fallback encodings
        for encoding in ['latin1', 'iso-8859-1', 'cp1252']:
            try:
                return text_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue

        # Last resort: decode with replacement
        return text_bytes.decode('utf-8', errors='replace')

    def get_email_body(self, email_message) -> str:
        """Extract email body with better encoding handling"""
        body = ""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = self.decode_text(payload)
                        break
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body = self.decode_text(payload)
        
        return body

    async def check_emails(self, folder: str = "INBOX",
                          criteria: Dict = None,
                          batch_size: int = None,
                          max_messages: int = None,
                          start_id: str = None) -> Dict:
        """Check for emails in specified folder with pagination using UIDs"""
        try:
            batch_size = batch_size or self.default_batch_size
            max_messages = max_messages or self.default_max_messages
            
            server = self.connect()
            server.select(folder)
            
            # Build search criteria
            search_criteria = self.build_search_criteria(criteria, start_id)
            logger.info(f"Using search criteria: {search_criteria}")
            
            # Use UID SEARCH instead of regular SEARCH
            _, data = server.uid('search', None, search_criteria)
            message_uids = data[0].split()
            
            # Sort UIDs in descending order (newest first)
            message_uids = sorted([int(uid) for uid in message_uids], reverse=True)
            total_messages = len(message_uids)
            
            logger.info(f"Found {total_messages} total messages")
            
            # Take the next batch of UIDs
            batch_uids = message_uids[:batch_size]
            
            email_list = []
            for uid in batch_uids:
                try:
                    # Use UID FETCH instead of regular FETCH
                    _, msg_data = server.uid('fetch', str(uid), '(RFC822)')
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)

                    # Extract body with safe decoding
                    body = self.get_email_body(email_message)

                    email_data = {
                        "id": str(uid),  # Use UID as the message ID
                        "message_id": email_message['Message-ID'],
                        "in_reply_to": email_message['In-Reply-To'],
                        "from": email_message['from'],
                        "to": email_message['to'],
                        "subject": email_message['subject'],
                        "date": email_message['date'],
                        "body": body
                    }

                    email_list.append(email_data)
                except Exception as e:
                    logger.error(f"Error processing message UID {uid}: {str(e)}")
                    continue

            server.close()
            server.logout()

            # Determine if there are more messages and next starting point
            has_more = len(message_uids) > batch_size
            next_id = str(batch_uids[-1] - 1) if has_more else None

            return {
                "success": True,
                "messages": email_list,
                "error": None,
                "pagination": {
                    "total_messages": total_messages,
                    "batch_size": batch_size,
                    "next_id": next_id,
                    "has_more": has_more
                }
            }

        except Exception as e:
            logger.error(f"Error checking emails: {str(e)}")
            return {
                "success": False,
                "messages": [],
                "error": str(e),
                "pagination": None
            }

    async def mark_as_processed(self, message_ids: List[str],
                              folder: str = "INBOX") -> Dict:
        """Mark messages as processed/read using UIDs"""
        try:
            server = self.connect()
            server.select(folder)

            processed = []
            failed = []

            for msg_id in message_ids:
                try:
                    # Use UID STORE instead of regular STORE
                    server.uid('store', msg_id, '+FLAGS', '\\Seen')
                    processed.append(msg_id)
                except Exception as e:
                    logger.error(f"Error marking message UID {msg_id}: {str(e)}")
                    failed.append(msg_id)

            server.close()
            server.logout()

            return {
                "success": len(failed) == 0,
                "processed": processed,
                "failed": failed,
                "error": None if len(failed) == 0 else "Some messages failed to mark"
            }

        except Exception as e:
            logger.error(f"Error marking messages: {str(e)}")
            return {
                "success": False,
                "processed": [],
                "failed": message_ids,
                "error": str(e)
            }
