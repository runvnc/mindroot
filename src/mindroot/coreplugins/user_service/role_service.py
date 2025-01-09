import os
import json
from typing import List
from lib.providers.services import service
from .models import UserAuth

@service()
async def has_role(username: str, role: str, user_data_root: str) -> bool:
    """Check if user has specified role"""
    auth_file = os.path.join(user_data_root, username, "auth.json")
    if not os.path.exists(auth_file):
        return False
        
    with open(auth_file, 'r') as f:
        try:
            auth_data = UserAuth(**json.load(f))
            return role in auth_data.roles
        except:
            return False

@service()
async def add_role(username: str, role: str, user_data_root: str) -> bool:
    """Add a role to a user. Should be called only from admin context."""
    auth_file = os.path.join(user_data_root, username, "auth.json")
    if not os.path.exists(auth_file):
        return False
        
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    
    # Add the role if it doesn't exist
    if role not in auth_data.roles:
        auth_data.roles.add(role)
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
    
    return True

@service()
async def remove_role(username: str, role: str, user_data_root: str) -> bool:
    """Remove a role from a user. Should be called only from admin context."""
    if role == "user":
        raise ValueError("Cannot remove 'user' role")
        
    auth_file = os.path.join(user_data_root, username, "auth.json")
    if not os.path.exists(auth_file):
        return False
        
    with open(auth_file, 'r') as f:
        auth_data = UserAuth(**json.load(f))
    
    # Remove the role if it exists
    if role in auth_data.roles:
        auth_data.roles.remove(role)
        with open(auth_file, 'w') as f:
            json.dump(auth_data.dict(), f, indent=2, default=str)
    
    return True

@service()
async def get_user_roles(username: str, user_data_root: str) -> List[str]:
    """Get all roles for a user"""
    auth_file = os.path.join(user_data_root, username, "auth.json")
    if not os.path.exists(auth_file):
        return set()
        
    with open(auth_file, 'r') as f:
        try:
            auth_data = UserAuth(**json.load(f))
            return auth_data.roles
        except:
            return ["user"]

