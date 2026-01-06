from typing import Dict, List
from .smtp_handler import SMTPHandler
from .imap_handler import IMAPHandler
import logging

logger = logging.getLogger(__name__)

class EmailProvider:
    def __init__(self, config: Dict):
        self.config = config
        self.smtp = SMTPHandler(config)
        self.imap = IMAPHandler(config)

    async def send_email(self, to: str, subject: str, body: str,
                        reply_to_message: Dict = None,
                        headers: Dict = None) -> Dict:
        """Send an email using SMTP"""
        return await self.smtp.send_email(
            to=to,
            subject=subject,
            body=body,
            reply_to_message=reply_to_message,
            headers=headers
        )

    async def check_emails(self, folder: str = "INBOX",
                          criteria: Dict = None,
                          batch_size: int = None,
                          max_messages: int = None,
                          start_id: str = None) -> Dict:
        """Check for emails using IMAP"""
        return await self.imap.check_emails(
            folder=folder,
            criteria=criteria,
            batch_size=batch_size,
            max_messages=max_messages,
            start_id=start_id
        )

    async def mark_as_processed(self, message_ids: List[str],
                              folder: str = "INBOX") -> Dict:
        """Mark messages as processed using IMAP"""
        return await self.imap.mark_as_processed(
            message_ids=message_ids,
            folder=folder
        )
