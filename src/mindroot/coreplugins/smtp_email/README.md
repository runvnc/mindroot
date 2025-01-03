# SMTP Email Provider for MindRoot

Core plugin providing SMTP email functionality for MindRoot.

## Configuration

Set the following environment variables:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_FROM="MindRoot <noreply@yourdomain.com>"

REQUIRE_EMAIL_VERIFY=true

```

### Provider Options

#### Gmail
1. Enable 2-factor authentication
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Create new app password
   - Use this as your SMTP_PASS

#### Google Workspace (Custom Domain)
1. Use your domain email (e.g., contact@yourbusiness.com)
2. SMTP settings:
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=contact@yourbusiness.com
   SMTP_PASS=your-app-password  # Generated same way as Gmail
   SMTP_FROM="Your Business <contact@yourbusiness.com>"
   ```

#### Other Email Providers
Works with any SMTP provider, examples:
- Microsoft 365
- Amazon SES
- SendGrid SMTP
- Custom mail server

Just use the appropriate SMTP settings provided by your email service.

## Usage

The plugin provides a `send_email` service that can be used by other plugins:

```python
from lib.providers.services import service_manager
from mindroot.coreplugins.smtp_email.mod import EmailMessage

await service_manager.send_email(EmailMessage(
    to="user@example.com",
    subject="Test Email",
    body="<h1>Hello World</h1>",
    html=True
))
```

## Features

- HTML and plain text email support
- Async implementation using aiosmtplib
- Automatic plain text version generation from HTML
- Error handling and logging
- Support for all SMTP providers
- Custom domain support
- Business email integration

## Security

- Uses TLS encryption
- Supports app-specific passwords
- Environment variable configuration
- No hardcoded credentials

## Common SMTP Settings

### Microsoft 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
```

### Amazon SES
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com  # Region specific
SMTP_PORT=587
```

### SendGrid
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
```
