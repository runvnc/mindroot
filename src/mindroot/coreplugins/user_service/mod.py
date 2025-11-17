from lib.providers.services import service
from .models import UserAuth, UserCreate, UserBase
from .email_service import send_verification_email, setup_verification
from .role_service import has_role, add_role, remove_role, get_user_roles
import bcrypt
import json
import os
from datetime import datetime
from typing import Optional, List
USER_DATA_ROOT = 'data/users'

@service()
async def create_user(user_data: UserCreate, roles: List[str]=None, skip_verification: bool=False, context=None) -> UserBase:
    """Create new user directory and auth file"""
    user_dir = os.path.join(USER_DATA_ROOT, user_data.username)
    os.makedirs(USER_DATA_ROOT, exist_ok=True)
    if os.path.exists(user_dir):
        raise ValueError('Username already exists')
    os.makedirs(user_dir)
    verification_token, verification_expires, email_verified = setup_verification()
    if verification_token and (not skip_verification):
        await send_verification_email(user_data.email, verification_token)
    if roles is None:
        roles = ['user']
    else:
        roles.append('user')
    now = datetime.utcnow().isoformat()
    auth_data = UserAuth(username=user_data.username, email=user_data.email, password_hash=bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt()).decode(), created_at=now, last_login=None, email_verified=email_verified, verification_token=verification_token, verification_expires=verification_expires, roles=roles)
    with open(os.path.join(user_dir, 'auth.json'), 'w') as f:
        json.dump(auth_data.dict(), f, indent=2, default=str)
    with open(os.path.join(user_dir, 'settings.json'), 'w') as f:
        json.dump({}, f)
    with open(os.path.join(user_dir, 'workspace.json'), 'w') as f:
        json.dump({}, f)
    return UserBase(**auth_data.dict())

@service()
async def verify_user(username: str, password: str, context=None) -> bool:
    """Verify user credentials and update last login"""
    auth_file = os.path.join(USER_DATA_ROOT, username, 'auth.json')
    if not os.path.exists(auth_file):
        return False
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    if bcrypt.checkpw(password.encode(), auth_data.password_hash.encode()):
        auth_data.last_login = datetime.utcnow().isoformat()
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
        return True
    else:
        return False

@service()
async def get_user_data(username: str, include_email=False, context=None) -> Optional[UserBase]:
    """Get user data excluding sensitive info"""
    auth_file = os.path.join(USER_DATA_ROOT, username, 'auth.json')
    if not os.path.exists(auth_file):
        return None
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    if not include_email:
        auth_data.email = None
    return UserBase(**auth_data.dict())

@service()
async def verify_email(token: str, context=None) -> bool:
    """Verify a user's email using their verification token"""
    if not os.environ.get('REQUIRE_EMAIL_VERIFY', '').lower() == 'true':
        return True
    for username in os.listdir(USER_DATA_ROOT):
        auth_file = os.path.join(USER_DATA_ROOT, username, 'auth.json')
        if os.path.exists(auth_file):
            with open(auth_file, 'r') as f:
                auth_data = UserAuth(**json.load(f))
            if auth_data.verification_token == token and auth_data.verification_expires and (datetime.fromisoformat(auth_data.verification_expires) > datetime.utcnow()):
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
    return [d for d in os.listdir(USER_DATA_ROOT) if os.path.isdir(os.path.join(USER_DATA_ROOT, d))]