# MindRoot Email Verification Setup Guide

## Overview
This guide explains how to set up email verification for MindRoot user accounts using Gmail SMTP.

## Issues Fixed

### 1. Email Service Registration
- Fixed email plugin services not being properly registered
- Added proper `@service()` decorators to email functions
- Implemented automatic email provider initialization

### 2. Email Sending Implementation
- Fixed incomplete `send_verification_email()` function
- Added HTML email support
- Improved error handling and logging
- Added password reset email functionality

### 3. Configuration Management
- Added environment variable support for email configuration
- Made BASE_URL configurable for verification links
- Added proper fallback handling

## Gmail SMTP Setup

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification if not already enabled

### Step 2: Generate App Password
1. In Google Account Security settings
2. Go to "App passwords" (under 2-Step Verification)
3. Select "Mail" as the app
4. Select "Other" as the device and name it "MindRoot"
5. Copy the generated 16-character password

### Step 3: Set Environment Variables

Add these to your environment (e.g., in `.env` file or shell):

```bash
# Required for email functionality
export SMTP_EMAIL="your-email@gmail.com"
export SMTP_PASSWORD="your-16-char-app-password"

# Optional - defaults shown
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USE_TLS="true"

# For email verification links
export BASE_URL="http://localhost:8011"  # Change for production
export REQUIRE_EMAIL_VERIFY="true"  # Set to "false" to disable verification
```

### Step 4: Test Email Service

Run the test script to verify your setup:

```bash
cd /files/mindroot
python src/mindroot/coreplugins/email/test_email_service.py
```

## Email Verification Flow

### User Registration
1. User fills out signup form at `/signup`
2. `create_user` service is called with user data
3. If `REQUIRE_EMAIL_VERIFY=true`, verification email is sent
4. User account is created with `email_verified=false`

### Email Verification
1. User clicks verification link in email
2. Link goes to `/verify-email?token=...` (handled by signup plugin)
3. Token is validated and user's `email_verified` status is updated
4. User is redirected to login with success message

### Login Behavior
- If email verification is required but not completed, user cannot log in
- Check `email_verified` field in user authentication

## File Structure

```
src/mindroot/coreplugins/
├── email/
│   ├── mod.py                    # Email services (fixed)
│   ├── smtp_handler.py           # SMTP implementation (updated)
│   ├── email_provider.py         # Email provider class
│   └── test_email_service.py     # Test script (new)
├── user_service/
│   ├── email_service.py          # Email verification logic (fixed)
│   ├── mod.py                    # User management services
│   └── models.py                 # User data models
└── signup/
    └── router.py                 # Signup and verification routes
```

## Key Functions

### Email Services (`email/mod.py`)
- `init_email_provider()` - Initialize SMTP connection
- `send_email()` - Send emails with HTML support
- `check_emails()` - Check incoming emails (IMAP)

### User Services (`user_service/mod.py`)
- `create_user()` - Create new user with email verification
- `verify_email()` - Verify email token and update user
- `get_user_data()` - Retrieve user information

### Email Verification (`user_service/email_service.py`)
- `send_verification_email()` - Send verification email
- `send_password_reset_email()` - Send password reset email
- `setup_verification()` - Generate verification tokens

## Troubleshooting

### Common Issues

1. **"Email provider not initialized"**
   - Check SMTP_EMAIL and SMTP_PASSWORD environment variables
   - Run the test script to verify configuration

2. **"Authentication failed"**
   - Ensure 2-factor authentication is enabled on Gmail
   - Use app password, not regular Gmail password
   - Check that app password is exactly 16 characters

3. **"Connection refused"**
   - Check SMTP_SERVER and SMTP_PORT settings
   - Verify firewall/network allows outbound SMTP connections

4. **Verification emails not received**
   - Check spam/junk folder
   - Verify BASE_URL is correct for your deployment
   - Check server logs for email sending errors

### Debug Steps

1. Run the email test script
2. Check server logs for email-related errors
3. Verify environment variables are set correctly
4. Test with a simple email client using same credentials

## Production Considerations

1. **Security**
   - Use environment variables, never hardcode credentials
   - Consider using OAuth2 instead of app passwords
   - Use HTTPS for verification links

2. **Reliability**
   - Implement email queue for high volume
   - Add retry logic for failed sends
   - Monitor email delivery rates

3. **Configuration**
   - Set proper BASE_URL for your domain
   - Configure appropriate token expiration times
   - Set up proper DNS records (SPF, DKIM, DMARC)

## Testing Checklist

- [ ] Environment variables set correctly
- [ ] Email test script runs successfully
- [ ] User registration sends verification email
- [ ] Verification link works and updates user status
- [ ] Login requires email verification when enabled
- [ ] Password reset emails work (if implemented)
- [ ] HTML emails display properly
- [ ] Error handling works for invalid tokens

## Next Steps

After setup:
1. Test the complete user registration flow
2. Verify email templates look good
3. Test with different email providers
4. Set up monitoring for email delivery
5. Consider implementing email templates system
