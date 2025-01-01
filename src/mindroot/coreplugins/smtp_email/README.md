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
```

### Gmail Setup

If using Gmail:
1. Enable 2-factor authentication
2. Generate an App Password:
   - Go to Google Account settings
   - Security > 2-Step Verification > App passwords
   - Create new app password
   - Use this as your SMTP_PASS

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

## Security

- Uses TLS encryption
- Supports app-specific passwords
- Environment variable configuration
- No hardcoded credentials
