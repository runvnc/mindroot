from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from lib.route_decorators import public_route
from lib.providers.services import service_manager
from mindroot.coreplugins.jwt_auth.middleware import create_access_token
from mindroot.coreplugins.user_service.models import UserCreate
from google.auth.transport import requests
from google.oauth2 import id_token
import google_auth_oauthlib.flow
import os
import secrets
import json
from typing import Optional

router = APIRouter()

# OAuth 2.0 configuration
CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/google_auth/callback')

# OAuth2 flow configuration
CLIENT_CONFIG = {
    "web": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI]
    }
}

SCOPES = ['openid', 'email', 'profile']

# Store state tokens temporarily (in production, use Redis or similar)
state_tokens = {}

@router.get("/google_auth/login")
@public_route()
async def google_login(request: Request):
    """Initiate Google OAuth2 login flow"""
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Create flow instance
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES
    )
    flow.redirect_uri = REDIRECT_URI
    
    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        state=state,
        prompt='select_account'
    )
    
    # Store state token
    state_tokens[state] = True
    
    return RedirectResponse(url=authorization_url)

@router.get("/google_auth/callback")
@public_route()
async def google_callback(request: Request, code: str, state: str):
    """Handle Google OAuth2 callback"""
    # Verify state token
    if state not in state_tokens:
        return RedirectResponse(url="/login?error=Invalid+state+token")
    
    # Remove used state token
    del state_tokens[state]
    
    try:
        # Create flow instance
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            CLIENT_CONFIG,
            scopes=SCOPES,
            state=state
        )
        flow.redirect_uri = REDIRECT_URI
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=code)
        
        # Get user info from ID token
        credentials = flow.credentials
        request_session = requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            request_session,
            CLIENT_ID
        )
        
        # Extract user information
        google_id = id_info['sub']
        email = id_info['email']
        name = id_info.get('name', email.split('@')[0])
        email_verified = id_info.get('email_verified', False)
        
        # Create username from email or name
        username = f"google_{google_id[:8]}"
        
        # Check if user exists
        existing_user = await service_manager.get_user_data(username)
        
        if not existing_user:
            # Create new user
            user_data = UserCreate(
                username=username,
                email=email,
                password=secrets.token_urlsafe(32)  # Random password for OAuth users
            )
            
            # Create user with email already verified if Google verified it
            await service_manager.create_user(
                user_data,
                roles=["user"],
                skip_verification=email_verified
            )
            
            # Update user metadata with Google info
            user_dir = os.path.join("data/users", username)
            google_info = {
                "google_id": google_id,
                "name": name,
                "picture": id_info.get('picture', ''),
                "locale": id_info.get('locale', ''),
                "auth_method": "google_oauth"
            }
            with open(os.path.join(user_dir, "google_info.json"), 'w') as f:
                json.dump(google_info, f, indent=2)
        
        # Create JWT token
        user_data = await service_manager.get_user_data(username)
        access_token = create_access_token(data={"sub": username, **user_data.dict()})
        
        # Create response with redirect
        response = RedirectResponse(url="/", status_code=303)
        
        # Set cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=604800,  # 1 week
            httponly=True,
            samesite="Lax"
        )
        
        return response
        
    except Exception as e:
        print(f"Google OAuth error: {e}")
        import traceback
        traceback.print_exc()
        return RedirectResponse(
            url="/login?error=Google+authentication+failed",
            status_code=303
        )

@router.get("/google_auth/config_check")
@public_route()
async def config_check():
    """Check if Google OAuth is configured"""
    return {
        "configured": bool(CLIENT_ID and CLIENT_SECRET),
        "redirect_uri": REDIRECT_URI
    }
