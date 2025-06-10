from lib.providers.services import service
from .models import UserAuth, PasswordResetToken
import bcrypt
import json
import os
import secrets
from datetime import datetime, timedelta

USER_DATA_ROOT = "data/users"
RESET_TOKEN_VALIDITY_HOURS = 1

@service()
async def initiate_password_reset(username: str, is_admin_reset: bool = False, context=None) -> str:
    """Initiates a password reset, generates a token, and stores it."""
    user_dir = os.path.join(USER_DATA_ROOT, username)
    if not os.path.exists(user_dir):
        raise ValueError("User not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_VALIDITY_HOURS)

    reset_data = PasswordResetToken(
        token=token,
        expires_at=expires_at.isoformat(),
        is_admin_reset=is_admin_reset
    )

    reset_file_path = os.path.join(user_dir, "password_reset.json")
    with open(reset_file_path, 'w') as f:
        json.dump(reset_data.dict(), f, indent=2)

    # In a real application, you would email this token to the user.
    # For this implementation, we return it directly.
    return token

@service()
async def reset_password_with_token(token: str, new_password: str, context=None) -> bool:
    """Resets a user's password using a valid reset token."""
    for username in os.listdir(USER_DATA_ROOT):
        user_dir = os.path.join(USER_DATA_ROOT, username)
        reset_file_path = os.path.join(user_dir, "password_reset.json")

        if not os.path.exists(reset_file_path):
            continue

        with open(reset_file_path, 'r') as f:
            try:
                reset_data = PasswordResetToken(**json.load(f))
            except (json.JSONDecodeError, TypeError):
                continue

        if reset_data.token == token:
            if datetime.fromisoformat(reset_data.expires_at) < datetime.utcnow():
                os.remove(reset_file_path) # Expired token
                raise ValueError("Password reset token has expired.")

            auth_file_path = os.path.join(user_dir, "auth.json")
            if not os.path.exists(auth_file_path):
                os.remove(reset_file_path)
                raise FileNotFoundError("User auth file not found.")

            with open(auth_file_path, 'r+') as auth_file:
                auth_data_dict = json.load(auth_file)
                auth_data = UserAuth(**auth_data_dict)

                new_password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                auth_data.password_hash = new_password_hash

                if reset_data.is_admin_reset and 'admin' not in auth_data.roles:
                    auth_data.roles.append('admin')

                auth_file.seek(0)
                json.dump(auth_data.dict(), auth_file, indent=2, default=str)
                auth_file.truncate()

            os.remove(reset_file_path) # Invalidate token after use
            return True

    raise ValueError("Invalid password reset token.")
