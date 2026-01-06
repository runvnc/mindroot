from lib.providers.services import service
from pydantic import BaseModel, EmailStr
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
REQUIRE_EMAIL_VERIFY = os.environ.get('REQUIRE_EMAIL_VERIFY', 'false').lower() == 'true'
SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')
SMTP_FROM = os.environ.get('SMTP_FROM')
if REQUIRE_EMAIL_VERIFY and (not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM])):
    raise ValueError('Missing required SMTP environment variables')

class EmailMessage(BaseModel):
    """Email message data model"""
    to: EmailStr
    subject: str
    body: str
    html: bool = True

@service()
async def send_email(message: EmailMessage, context=None) -> bool:
    """Send an email using SMTP
    
    Args:
        message: EmailMessage containing to, subject, and body
        
    Returns:
        bool: True if email was sent successfully
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.subject
        msg['From'] = SMTP_FROM
        msg['To'] = message.to
        if message.html:
            plain = message.body.replace('<br>', '\n').replace('</p>', '\n\n')
            plain = ''.join((plain.split('<')[0] for plain in plain.split('>')))
            msg.attach(MIMEText(plain, 'plain'))
            msg.attach(MIMEText(message.body, 'html'))
        else:
            msg.attach(MIMEText(message.body, 'plain'))
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT, use_tls=True) as smtp:
            await smtp.login(SMTP_USER, SMTP_PASS)
            await smtp.send_message(msg)
        return True
    except Exception as e:
        return False