from lib.providers.services import service
from lib.providers.commands import command
from .models import UserAuth, UserCreate, UserBase
from mindroot.coreplugins.smtp_email.mod import EmailMessage
from lib.providers.services import service_manager
import bcrypt
import json
import os
from datetime import datetime, timedelta
from typing import Optional
import secrets

USER_DATA_ROOT = "data/users"
REQUIRE_EMAIL_VERIFY = os.environ.get('REQUIRE_EMAIL_VERIFY', '').lower() == 'true'

@service()
async def create_user(user_data: UserCreate, context=None) -> UserBase:
    """Create new user directory and auth file"""
    user_dir = os.path.join(USER_DATA_ROOT, user_data.username)
    
    # Ensure user data root exists
    os.makedirs(USER_DATA_ROOT, exist_ok=True)
    
    # Check if user exists
    if os.path.exists(user_dir):
        raise ValueError("Username already exists")
        
    # Create user directory
    os.makedirs(user_dir)
    
    # Handle verification based on configuration
    if REQUIRE_EMAIL_VERIFY:
        verification_token = secrets.token_urlsafe(32)
        verification_expires = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        email_verified = False
        
        # Send verification email
        verification_url = f"http://localhost:8011/verify-email?token={verification_token}"
        email_html = f"""
        <h1>Welcome to MindRoot!</h1>
        <p>Please verify your email address by clicking the link below:</p>
        <p><a href="{verification_url}">{verification_url}</a></p>
        <p>This link will expire in 24 hours.</p>
        <br>
        <p>If you did not create this account, please ignore this email.</p>
        """
        
        try:
            await service_manager.send_email(EmailMessage(
                to=user_data.email,
                subject="Verify Your MindRoot Account",
                body=email_html
            ))
        except Exception as e:
            print(f"Warning: Could not send verification email: {e}")
    else:
        verification_token = None
        verification_expires = None
        email_verified = True
    
    # Create auth data
    now = datetime.utcnow().isoformat()
    auth_data = UserAuth(
        username=user_data.username,
        email=user_data.email,
        password_hash=bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode(),
        created_at=now,
        last_login=None,
        email_verified=email_verified,
        verification_token=verification_token,
        verification_expires=verification_expires
    )
    
    # Save auth data
    with open(os.path.join(user_dir, "auth.json"), 'w') as f:
        json.dump(auth_data.dict(), f, indent=2, default=str)
        
    # Initialize empty settings and workspace
    with open(os.path.join(user_dir, "settings.json"), 'w') as f:
        json.dump({}, f)
    with open(os.path.join(user_dir, "workspace.json"), 'w') as f:
        json.dump({}, f)
    
    # Return safe user data
    return UserBase(**auth_data.dict())

@service()
async def verify_user(username: str, password: str, context=None) -> bool:
    """Verify user credentials and update last login"""
    auth_file = os.path.join(USER_DATA_ROOT, username, "auth.json")
    
    if not os.path.exists(auth_file):
        return False
        
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    
    if bcrypt.checkpw(password.encode(), auth_data.password_hash.encode()):
        # Update last login
        auth_data.last_login = datetime.utcnow().isoformat()
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
        return True
    return False

@service()
async def get_user_data(username: str, context=None) -> Optional[UserBase]:
    """Get user data excluding sensitive info"""
    auth_file = os.path.join(USER_DATA_ROOT, username, "auth.json")
    if not os.path.exists(auth_file):
        return None
        
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    
    # Return safe user data
    return UserBase(**auth_data.dict())

@service()
async def verify_email(token: str, context=None) -> bool:
    """Verify a user's email using their verification token"""
    if not REQUIRE_EMAIL_VERIFY:
        return True
        
    # Search through user directories for matching token
    for username in os.listdir(USER_DATA_ROOT):
        auth_file = os.path.join(USER_DATA_ROOT, username, "auth.json")
        if os.path.exists(auth_file):
            with open(auth_file, 'r') as f:
                auth_data = UserAuth(**json.load(f))
            
            if (auth_data.verification_token == token and 
                auth_data.verification_expires and
                datetime.fromisoformat(auth_data.verification_expires) > datetime.utcnow()):
                
                # Update user as verified
                auth_data.email_verified = True
                auth_data.verification_token = None
                auth_data.verification_expires = None
                
                with open(auth_file, 'w') as f:
                    json.dump(auth_data.dict(), f, indent=2, default=str)
                
                return True
    
    return False

@service()
async def list_users(context=None) -> list[str]:
    """List all usernames"""
    if not os.path.exists(USER_DATA_ROOT):
        return []
    return [d for d in os.listdir(USER_DATA_ROOT) 
            if os.path.isdir(os.path.join(USER_DATA_ROOT, d))]

# Also expose some functions as commands for admin use
@command()
async def list_users_command(params, context=None):
    """List all users in the system.
    
    Example:
    { "list_users_command": {} }
    """
    return await list_users()

@command()
async def get_user_command(params, context=None):
    """Get user data for a specific user.
    
    Example:
    { "get_user_command": { "username": "testuser" } }
    """
    username = params.get("username")
    if not username:
        raise ValueError("Username parameter required")
    return await get_user_data(username)
