from lib.providers.services import service
from lib.providers.commands import command
from .models import UserAuth, UserCreate, UserBase
import bcrypt
import json
import os
from datetime import datetime
from typing import Optional

USER_DATA_ROOT = "data/users"

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
    
    # Create auth data
    now = datetime.utcnow()
    auth_data = UserAuth(
        username=user_data.username,
        email=user_data.email,
        password_hash=bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode(),
        created_at=now,
        last_login=None
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
        auth_data.last_login = datetime.utcnow()
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
