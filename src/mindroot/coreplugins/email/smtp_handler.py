import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class SMTPHandler:
    def __init__(self, config: Dict):
        self.smtp_server = config['smtp_server']
        self.smtp_port = config['smtp_port']
        self.use_tls = config.get('use_tls', True)
        self.email = config['email']
        self.password = config['password']

    async def connect(self) -> smtplib.SMTP:
        """Establish SMTP connection"""
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.email, self.password)
            return server
        except Exception as e:
            logger.error(f"SMTP Connection error: {str(e)}")
            raise

    async def send_email(self, to: str, subject: str, body: str,
                        reply_to_message: Dict = None,
                        headers: Dict = None) -> Dict:
        """Send an email"""
        try:
            server = await self.connect()
            
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to
            msg['Subject'] = subject

            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value

            # Add reply headers if this is a reply
            if reply_to_message:
                msg['In-Reply-To'] = reply_to_message['message_id']
                if not subject.lower().startswith('re:'):
                    msg['Subject'] = f"Re: {subject}"

            msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            server.quit()

            return {
                "success": True,
                "message_id": msg['Message-ID'],
                "error": None
            }

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "message_id": None,
                "error": str(e)
            }
