"""
Test script to verify email service functionality.
Run this to test if email sending works with your configuration.
"""
import asyncio
import os
import sys
sys.path.append('/files/mindroot/src')
from mindroot.coreplugins.email.mod import init_email_provider, send_email

async def test_email_service():
    """Test the email service with current environment configuration"""
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    if not smtp_email or not smtp_password:
        return False
    success = await init_email_provider()
    if not success:
        return False
    test_email = input(f'Enter test email address (or press Enter to use {smtp_email}): ').strip()
    if not test_email:
        test_email = smtp_email
    html_body = '\n    <html>\n    <body>\n        <h1>MindRoot Email Service Test</h1>\n        <p>This is a test email from MindRoot.</p>\n        <p><strong>HTML formatting works!</strong></p>\n        <p>If you can see this styled content, HTML emails are working correctly.</p>\n    </body>\n    </html>\n    '
    result = await send_email(to=test_email, subject='MindRoot Email Service Test', body=html_body)
    if result.get('success'):
        return True
    else:
        return False
if __name__ == '__main__':
    asyncio.run(test_email_service())