# Gmail/Google Workspace Custom Domain Setup for MindRoot

## Overview
The existing MindRoot SMTP code already supports custom domains. You just need to configure Gmail/Google Workspace properly and set the right environment variables.

## Option 1: Google Workspace (Recommended for Custom Domains)

### Prerequisites
- Google Workspace account with your custom domain (mindroot.io)
- Admin access to your Google Workspace

### Setup Steps

1. **Create Email Account**
   - In Google Workspace Admin Console
   - Go to Users → Add User
   - Create: `no-reply@mindroot.io`
   - Set a strong password

2. **Enable 2-Factor Authentication**
   - Sign in as `no-reply@mindroot.io`
   - Go to Google Account → Security
   - Enable 2-Step Verification

3. **Generate App Password**
   - In Security settings → App passwords
   - Select "Mail" and "Other (custom name)"
   - Name it "MindRoot SMTP"
   - Copy the 16-character password

4. **Set Environment Variables**
   ```bash
   export SMTP_EMAIL="no-reply@mindroot.io"
   export SMTP_PASSWORD="your-16-char-app-password"
   export SMTP_SERVER="smtp.gmail.com"  # Same as regular Gmail
   export SMTP_PORT="587"
   export SMTP_USE_TLS="true"
   export BASE_URL="https://yourdomain.com"  # Your actual domain
   export REQUIRE_EMAIL_VERIFY="true"
   ```

## Option 2: Regular Gmail with Custom Domain (Limited)

### Prerequisites
- Regular Gmail account
- Custom domain with email forwarding set up

### Setup Steps

1. **Configure Gmail to Send As Custom Domain**
   - In Gmail → Settings → Accounts and Import
   - Click "Add another email address"
   - Add: `no-reply@mindroot.io`
   - Choose "Send through Gmail's servers"
   - Verify ownership via email forwarding

2. **Enable 2-Factor Authentication**
   - On your main Gmail account
   - Google Account → Security → 2-Step Verification

3. **Generate App Password**
   - Security → App passwords
   - Select "Mail" → "Other"
   - Copy 16-character password

4. **Set Environment Variables**
   ```bash
   export SMTP_EMAIL="no-reply@mindroot.io"  # Custom domain
   export SMTP_PASSWORD="your-16-char-app-password"  # From main Gmail
   export SMTP_SERVER="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USE_TLS="true"
   export BASE_URL="https://yourdomain.com"
   export REQUIRE_EMAIL_VERIFY="true"
   ```

## Testing Your Setup

1. **Test with the existing script:**
   ```bash
   cd /files/mindroot
   python src/mindroot/coreplugins/email/test_email_service.py
   ```

2. **Verify the "From" address:**
   - The test email should show as coming from `no-reply@mindroot.io`
   - Check both the sender and reply-to fields

## Multi-Tenant Support (For Other Users)

For other users with their own domains, they just need to set their own environment variables:

```bash
# User 1 with their domain
export SMTP_EMAIL="noreply@theircompany.com"
export SMTP_PASSWORD="their-app-password"
export BASE_URL="https://theircompany.com"

# User 2 with different domain
export SMTP_EMAIL="system@anotherdomain.org"
export SMTP_PASSWORD="another-app-password"
export BASE_URL="https://anotherdomain.org"
```

## Important Notes

### Google Workspace vs Regular Gmail
- **Google Workspace**: Native support for custom domains, better for business use
- **Regular Gmail**: Requires "Send As" setup, may have limitations

### DNS Considerations
For better email deliverability with custom domains:

1. **SPF Record** (Add to your DNS):
   ```
   v=spf1 include:_spf.google.com ~all
   ```

2. **DKIM** (Enable in Google Workspace Admin):
   - Go to Apps → Google Workspace → Gmail
   - Authenticate email → Generate new record
   - Add the DKIM record to your DNS

3. **DMARC Record** (Optional but recommended):
   ```
   v=DMARC1; p=quarantine; rua=mailto:dmarc@mindroot.io
   ```

### Security Best Practices
- Use app passwords, never regular passwords
- Rotate app passwords periodically
- Monitor email sending logs
- Set up proper DNS records for deliverability

## Troubleshooting

### Common Issues

1. **"Authentication failed" with custom domain**
   - Verify the app password is from the correct Google account
   - For Gmail "Send As", use the main Gmail account's app password
   - For Google Workspace, use the custom domain account's app password

2. **Emails going to spam**
   - Set up SPF, DKIM, and DMARC records
   - Warm up the sending domain gradually
   - Avoid spam trigger words in subject lines

3. **"Send As" not working**
   - Verify domain ownership in Gmail settings
   - Check that email forwarding is working
   - May need to verify via DNS TXT record instead

### Testing Checklist
- [ ] Environment variables set with custom domain
- [ ] Test script sends email successfully
- [ ] Email shows correct "From" address
- [ ] Verification links use correct BASE_URL
- [ ] SPF/DKIM records configured (if using Google Workspace)
- [ ] Test complete signup → verification flow

## No Code Changes Required!

The existing MindRoot SMTP implementation already supports:
- Custom "From" addresses
- HTML email content
- Proper error handling
- Environment variable configuration

Just configure your Gmail/Google Workspace and set the environment variables correctly.
