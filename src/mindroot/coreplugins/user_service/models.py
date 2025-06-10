from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Set

class UserBase(BaseModel):
    """Base user data that's safe to expose"""
    username: str = Field(..., min_length=3, max_length=32)
    email: Optional[EmailStr]
    created_at: str
    last_login: Optional[str] = None
    email_verified: bool = False
    roles: List[str] = Field(default_factory=lambda: ["user"])  # Default role is 'user'

class UserAuth(UserBase):
    """User data including auth-sensitive fields"""
    password_hash: str
    verification_token: Optional[str] = None
    verification_expires: Optional[str] = None

class UserCreate(BaseModel):
    """Data required to create a new user"""
    username: str = Field(..., min_length=3, max_length=32, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserInRequest(UserBase):
    """User data as attached to request.state.user"""
    token_data: dict


class PasswordResetToken(BaseModel):
    """Data for password reset tokens"""
    token: str
    expires_at: str
    is_admin_reset: bool = False
