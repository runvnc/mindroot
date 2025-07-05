#!/usr/bin/env python3
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
    print("Testing email service...")
    
    # Check environment variables
    smtp_email = os.getenv('SMTP_EMAIL')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_email or not smtp_password:
        print("❌ Missing SMTP_EMAIL or SMTP_PASSWORD environment variables")
        print("Please set these environment variables:")
        print("  export SMTP_EMAIL='your-email@gmail.com'")
        print("  export SMTP_PASSWORD='your-app-password'")
        return False
    
    print(f"📧 Using SMTP email: {smtp_email}")
    
    # Initialize email provider
    print("Initializing email provider...")
    success = await init_email_provider()
    
    if not success:
        print("❌ Failed to initialize email provider")
        return False
    
    print("✅ Email provider initialized successfully")
    
    # Test sending email
    test_email = input(f"Enter test email address (or press Enter to use {smtp_email}): ").strip()
    if not test_email:
        test_email = smtp_email
    
    print(f"Sending test email to {test_email}...")
    
    # Test HTML email
    html_body = """
    <html>
    <body>
        <h1>MindRoot Email Service Test</h1>
        <p>This is a test email from MindRoot.</p>
        <p><strong>HTML formatting works!</strong></p>
        <p>If you can see this styled content, HTML emails are working correctly.</p>
    </body>
    </html>
    """
    
    result = await send_email(
        to=test_email,
        subject="MindRoot Email Service Test",
        body=html_body  # HTML will be auto-detected
    )
    
    if result.get('success'):
        print("✅ Test email sent successfully!")
        print(f"Message ID: {result.get('message_id')}")
        return True
    else:
        print(f"❌ Failed to send test email: {result.get('error')}")
        return False

if __name__ == "__main__":
    asyncio.run(test_email_service())
