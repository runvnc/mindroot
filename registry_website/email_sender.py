import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict

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
                        headers: Dict = None) -> Dict:
        """Send an email"""
        try:
            server = await self.connect()
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = to
            msg['Subject'] = subject

            if headers:
                for key, value in headers.items():
                    msg[key] = value

            if '<html>' in body.lower() or '<p>' in body.lower() or '<br>' in body.lower():
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            server.send_message(msg)
            server.quit()

            return {"success": True, "error": None}

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}

async def send_verification_email(email: str, token: str):
    """Sends a verification email using SMTP settings from environment variables."""
    config = {
        'smtp_server': os.getenv('SMTP_SERVER'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'email': os.getenv('SMTP_EMAIL'),
        'password': os.getenv('SMTP_PASSWORD'),
    }

    if not all([config['smtp_server'], config['email'], config['password']]):
        logger.error("SMTP environment variables not set. Cannot send verification email.")
        # In a real scenario, you might want to raise an exception or handle this more gracefully
        return {"success": False, "error": "SMTP settings not configured on the server."}

    smtp_handler = SMTPHandler(config)
    
    # The verification link should point to your deployed registry's domain
    # Using localhost for now, but this should be an env var in production
    registry_url = os.getenv('REGISTRY_URL', 'https://registry.mindroot.io')
    verification_link = f"{registry_url}/verify-email/{token}"
    
    subject = "Verify Your MindRoot Registry Account"
    body = f"""\
    <html>
        <body>
            <h2>Welcome to the MindRoot Registry!</h2>
            <p>Please click the link below to verify your email address and activate your account:</p>
            <p><a href='{verification_link}'>Verify My Email</a></p>
            <p>If you did not create an account, please ignore this email.</p>
        </body>
    </html>
    """

    return await smtp_handler.send_email(to=email, subject=subject, body=body)
