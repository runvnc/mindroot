import os
import random
import string
from typing import Tuple, Optional
from pathlib import Path
import json
from datetime import datetime
from lib.providers.hooks import hook
from .models import UserAuth, UserCreate
from .role_service import has_role
from .mod import create_user
from lib.providers.services import service
from rich.console import Console
console = Console()
USER_DATA_ROOT = 'data/users'
created_admin = {}

@hook()
async def startup(app, context):
    admin_user, admin_pass = await initialize_admin(USER_DATA_ROOT, app)
    if admin_user:
        created_admin['username'] = admin_user
        created_admin['password'] = admin_pass
        console.print(f"Created admin user: {created_admin['username']} password: {created_admin['password']}", style='yellow on dark_blue')

def generate_random_credentials(prefix: str='admin', length: int=8) -> Tuple[str, str]:
    """Generate random admin username and password."""
    chars = string.ascii_letters + string.digits
    random_suffix = ''.join(random.choices(chars, k=length))
    random_pass = ''.join(random.choices(chars + '!@#$%^&*', k=16))
    return (f'{prefix}{random_suffix}', random_pass)

async def check_for_admin(user_data_root: str) -> bool:
    """Check if any admin user exists."""
    if not os.path.exists(user_data_root):
        return False
    for username in os.listdir(user_data_root):
        auth_file = os.path.join(user_data_root, username, 'auth.json')
        if os.path.exists(auth_file):
            with open(auth_file, 'r') as f:
                try:
                    auth_data = UserAuth(**json.load(f))
                    if 'admin' in auth_data.roles:
                        return True
                except:
                    continue
    return False

@service()
async def initialize_admin(user_data_root: str, app) -> Tuple[Optional[str], Optional[str]]:
    """Check for and create admin user if needed.
    Returns tuple of (username, password) if created, (None, None) if admin exists.
    
    This should be called during system startup to ensure at least one admin exists.
    The admin user will have 'admin', 'verified', and 'user' roles.
    """
    args = app.state.cmd_args
    username = None
    password = None
    admin_user = None
    admin_pass = None
    if args.admin_user:
        admin_user = args.admin_user
        admin_pass = args.admin_password
    if admin_user and admin_pass:
        username = admin_user
        password = admin_pass
    else:
        if await check_for_admin(user_data_root):
            return (None, None)
        env_user = os.environ.get('ADMIN_USER')
        env_pass = os.environ.get('ADMIN_PASS')
        username = env_user
        password = env_pass
        if not (username and password):
            username, password = generate_random_credentials()
            username = 'admin'
    user_data = UserCreate(username=username, password=password, email=os.environ.get('ADMIN_EMAIL', 'admin@admin.com'))
    try:
        await create_user(user_data, roles=['admin', 'verified'], skip_verification=True)
    except Exception as e:
        if 'exists' in str(e):
            pass
        else:
            raise e
    return (username, password)