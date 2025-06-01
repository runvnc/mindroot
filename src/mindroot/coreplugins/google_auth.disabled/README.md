# Google OAuth Authentication Plugin

This plugin adds Google Sign-In functionality to MindRoot, allowing users to authenticate using their Google accounts.

## Setup Instructions

### 1. Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API for your project
4. Go to "Credentials" in the left sidebar
5. Click "Create Credentials" > "OAuth client ID"
6. Select "Web application" as the application type
7. Add your redirect URI (e.g., `http://localhost:8000/google_auth/callback` for local development)
8. Save your Client ID and Client Secret

### 2. Configure Environment Variables

Add the following to your `.env` file in the MindRoot root directory:

```bash
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/google_auth/callback
```

For production, update `GOOGLE_REDIRECT_URI` to your actual domain:
```bash
GOOGLE_REDIRECT_URI=https://yourdomain.com/google_auth/callback
```

### 3. Update Google OAuth Authorized Redirect URIs

Make sure to add your redirect URI to the authorized redirect URIs in your Google OAuth client settings.

## How It Works

1. Users click "Sign in with Google" on the login page
2. They are redirected to Google's OAuth consent screen
3. After authorization, Google redirects back to `/google_auth/callback`
4. The plugin:
   - Verifies the OAuth response
   - Creates a new user account if needed (username: `google_[partial_google_id]`)
   - Sets the same JWT token used by the regular login system
   - Redirects to the home page

## User Data

When a user signs in with Google:
- A new user account is created with a generated username
- Their Google email is stored
- Email is automatically verified if Google has verified it
- Additional Google profile info is stored in `google_info.json`

## Security Notes

- State tokens are used to prevent CSRF attacks
- Google ID tokens are verified server-side
- Users get the same JWT tokens as regular login
- Passwords for OAuth users are randomly generated and not used

## Troubleshooting

1. **"Google OAuth not configured" error**: Make sure you've set the environment variables
2. **Redirect URI mismatch**: Ensure the redirect URI in your `.env` matches exactly what's configured in Google Cloud Console
3. **Invalid state token**: This is a security feature - just try signing in again

## Integration with Existing System

The plugin integrates seamlessly with MindRoot's existing authentication:
- Uses the same JWT token system
- Compatible with existing middleware
- Users can access all the same features
- Admin can manage Google-authenticated users like any other users
