from typing import Dict, List, Optional
from .email_provider import EmailProvider

# Global provider instance
_provider = None

async def init_provider(config: Dict) -> None:
    """Initialize the email provider with config"""
    global _provider
    _provider = EmailProvider(config)

async def get_provider() -> EmailProvider:
    """Get the provider instance, initializing with defaults if needed"""
    global _provider
    if _provider is None:
        raise RuntimeError("Email provider not initialized. Call init_provider first.")
    return _provider

# Removed @service() decorator - this is now just a helper function
# The actual service is in mod.py
async def send_email_helper(config: Dict, to: str, subject: str, body: str,
               reply_to_message: Dict = None,
               headers: Dict = None) -> Dict:
    """Helper function to send an email (not a service)"""
    provider = await get_provider()
    return await provider.send_email(
        to=to,
        subject=subject,
        body=body,
        reply_to_message=reply_to_message,
        headers=headers
    )

async def check_emails(config: Dict, folder: str = "INBOX",
                criteria: Dict = None,
                batch_size: int = None,
                max_messages: int = None,
                start_id: str = None) -> Dict:
    """Service to check for new emails with pagination support"""
    provider = await get_provider()
    return await provider.check_emails(
        folder=folder,
        criteria=criteria,
        batch_size=batch_size,
        max_messages=max_messages,
        start_id=start_id
    )

async def mark_as_processed(config: Dict, message_ids: List[str],
                     folder: str = "INBOX") -> Dict:
    """Service to mark emails as processed"""
    provider = await get_provider()
    return await provider.mark_as_processed(
        message_ids=message_ids,
        folder=folder
    )
