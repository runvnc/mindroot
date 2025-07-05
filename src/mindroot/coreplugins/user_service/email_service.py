from lib.providers.services import service_manager
from datetime import datetime, timedelta
import secrets
import os
import logging

logger = logging.getLogger(__name__)

REQUIRE_EMAIL_VERIFY = os.environ.get('REQUIRE_EMAIL_VERIFY', '').lower() == 'true'
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8011')

async def send_verification_email(email: str, verification_token: str):
    """Send email verification link to user."""
    verification_url = f"{BASE_URL}/verify-email?token={verification_token}"
    
    email_html = f"""
    <html>
    <body>
        <h1>Welcome to MindRoot!</h1>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Verify Email</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p><code>{verification_url}</code></p>
        <p>This link will expire in 24 hours.</p>
        <br>
        <p><small>If you did not create this account, please ignore this email.</small></p>
    </body>
    </html>
    """
    
    try:
        result = await service_manager.send_email(
            to=email,
            subject="Verify Your MindRoot Account",
            body=email_html  # HTML content will be auto-detected
        )
        
        if result.get('success'):
            logger.info(f"Verification email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send verification email to {email}: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Exception sending verification email to {email}: {e}")
        return False

async def send_password_reset_email(email: str, username: str, reset_token: str):
    """Send password reset email to user."""
    reset_url = f"{BASE_URL}/reset-password?token={reset_token}"
    
    email_html = f"""
    <html>
    <body>
        <h1>Password Reset Request</h1>
        <p>Hello {username},</p>
        <p>You have requested to reset your password for your MindRoot account.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}" style="background-color: #f44336; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
        <p>Or copy and paste this link into your browser:</p>
        <p><code>{reset_url}</code></p>
        <p>This link will expire in 1 hour.</p>
        <br>
        <p><small>If you did not request this password reset, please ignore this email.</small></p>
    </body>
    </html>
    """
    
    try:
        result = await service_manager.send_email(
            to=email,
            subject="Password Reset Request - MindRoot",
            body=email_html  # HTML content will be auto-detected
        )
        
        if result.get('success'):
            logger.info(f"Password reset email sent successfully to {email}")
            return True
        else:
            logger.error(f"Failed to send password reset email to {email}: {result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Exception sending password reset email to {email}: {e}")
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
