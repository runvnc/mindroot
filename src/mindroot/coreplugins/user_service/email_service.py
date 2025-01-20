#from mindroot.coreplugins.email.mod import EmailMessage
from lib.providers.services import service_manager
from datetime import datetime, timedelta
import secrets
import os

REQUIRE_EMAIL_VERIFY = os.environ.get('REQUIRE_EMAIL_VERIFY', '').lower() == 'true'

async def send_verification_email(email: str, verification_token: str):
    """Send email verification link to user."""
    verification_url = f"http://localhost:8011/verify-email?token={verification_token}"
    email_html = f"""
    <h1>Welcome to MindRoot!</h1>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{verification_url}">{verification_url}</a></p>
    <p>This link will expire in 24 hours.</p>
    <br>
    <p>If you did not create this account, please ignore this email.</p>
    """
    print("Not implemented")
    return False   
    try:
        #await service_manager.send_email(EmailMessage(
        #    to=email,
        #    subject="Verify Your MindRoot Account",
        #    body=email_html
        #))
        return True
    except Exception as e:
        print(f"Warning: Could not send verification email: {e}")
        return False

def setup_verification() -> tuple[str, str, bool]:
    """Setup email verification token and expiry.
    Returns: (token, expiry timestamp, verified status)
    """
    if not REQUIRE_EMAIL_VERIFY:
        return None, None, True
        
    verification_token = secrets.token_urlsafe(32)
    verification_expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    return verification_token, verification_expires, False
