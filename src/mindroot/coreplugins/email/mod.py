from lib.providers.services import service
from .email_provider import EmailProvider
from .services import init_provider as _init_provider, get_provider as _get_provider
from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

# Global provider instance
_provider = None

@service()
async def init_email_provider(config: Dict = None, context=None) -> bool:
    """Initialize the email provider with config"""
    global _provider
    
    if config is None:
        # Use environment variables for default config
        config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            'email': os.getenv('SMTP_EMAIL', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'imap_server': os.getenv('IMAP_SERVER', 'imap.gmail.com'),
            'imap_port': int(os.getenv('IMAP_PORT', '993'))
        }
    
    if not config['email'] or not config['password']:
        logger.warning("Email provider not initialized: missing SMTP_EMAIL or SMTP_PASSWORD")
        return False
    
    try:
        _provider = EmailProvider(config)
        logger.info("Email provider initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize email provider: {e}")
        return False

@service()
async def send_email(to: str, subject: str, body: str, context=None) -> Dict:
    """Service to send an email
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (can be plain text or HTML - auto-detected)
        context: Optional context
    
    Returns:
        Dict with success status and error info
    """
    global _provider
    
    if _provider is None:
        # Try to initialize with default config
        success = await init_email_provider(context=context)
        if not success:
            return {
                "success": False,
                "error": "Email provider not initialized"
            }
    
    try:
        result = await _provider.send_email(
            to=to,
            subject=subject,
            body=body
        )
        return result
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@service()
async def check_emails(folder: str = "INBOX", criteria: Dict = None, context=None) -> Dict:
    """Service to check for new emails"""
    global _provider
    
    if _provider is None:
        success = await init_email_provider(context=context)
        if not success:
            return {
                "success": False,
                "error": "Email provider not initialized"
            }
    
    try:
        return await _provider.check_emails(folder=folder, criteria=criteria)
    except Exception as e:
        logger.error(f"Error checking emails: {e}")
        return {
            "success": False,
            "error": str(e)
        }
