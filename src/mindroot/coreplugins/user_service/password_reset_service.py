from typing import Optional
from lib.providers.services import service
from .models import UserAuth, PasswordResetToken
import bcrypt
import json
import os
import secrets
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

USER_DATA_ROOT = "data/users"
RESET_TOKEN_VALIDITY_HOURS = 1

@service()
async def initiate_password_reset(username: str, is_admin_reset: bool = False, token: Optional[str] = None, context=None) -> str:
    """Initiates a password reset, generates a token, and stores it."""
    # Log current working directory and absolute paths
    cwd = os.getcwd()
    abs_user_data_root = os.path.abspath(USER_DATA_ROOT)
    user_dir = os.path.join(USER_DATA_ROOT, username)
    abs_user_dir = os.path.abspath(user_dir)
    
    logger.info(f"=== PASSWORD RESET INITIATION ===")
    logger.info(f"Current working directory: {cwd}")
    logger.info(f"USER_DATA_ROOT (relative): {USER_DATA_ROOT}")
    logger.info(f"USER_DATA_ROOT (absolute): {abs_user_data_root}")
    logger.info(f"User directory (relative): {user_dir}")
    logger.info(f"User directory (absolute): {abs_user_dir}")
    logger.info(f"Initiating password reset for user: {username}")
    
    if not os.path.exists(user_dir):
        logger.error(f"User directory not found: {user_dir} (absolute: {abs_user_dir})")
        logger.error(f"Directory exists check: {os.path.exists(abs_user_dir)}")
        raise ValueError("User not found")

    # List existing files in user directory
    try:
        existing_files = os.listdir(user_dir)
        logger.info(f"Existing files in user directory: {existing_files}")
    except Exception as e:
        logger.error(f"Error listing user directory: {e}")

    if token is None:
        token = secrets.token_urlsafe(32)
    
    expires_at = datetime.utcnow() + timedelta(hours=RESET_TOKEN_VALIDITY_HOURS)
    logger.info(f"Generated reset token for {username}, expires at: {expires_at.isoformat()}")

    reset_data = PasswordResetToken(
        token=token,
        expires_at=expires_at.isoformat(),
        is_admin_reset=is_admin_reset
    )

    reset_file_path = os.path.join(user_dir, "password_reset.json")
    abs_reset_file_path = os.path.abspath(reset_file_path)
    logger.info(f"Saving reset token to: {reset_file_path} (absolute: {abs_reset_file_path})")
    
    with open(reset_file_path, 'w') as f:
        json.dump(reset_data.dict(), f, indent=2)
    
    logger.info(f"Reset token file created successfully")
    
    # Verify file was created
    if os.path.exists(reset_file_path):
        logger.info(f"Verified: Reset token file exists after creation")
        try:
            with open(reset_file_path, 'r') as f:
                verify_data = json.load(f)
                logger.info(f"Verified: Reset token file contents: {verify_data}")
        except Exception as e:
            logger.error(f"Error reading back reset token file: {e}")
    else:
        logger.error(f"ERROR: Reset token file was not created successfully!")
    
    return token

@service()
async def reset_password_with_token(token: str, new_password: str, context=None) -> bool:
    """Resets a user's password using a valid reset token."""
    # Log current working directory and absolute paths
    cwd = os.getcwd()
    abs_user_data_root = os.path.abspath(USER_DATA_ROOT)
    
    logger.info(f"=== PASSWORD RESET ATTEMPT ===")
    logger.info(f"Current working directory: {cwd}")
    logger.info(f"USER_DATA_ROOT (relative): {USER_DATA_ROOT}")
    logger.info(f"USER_DATA_ROOT (absolute): {abs_user_data_root}")
    logger.info(f"Attempting password reset with token: {token[:10]}...{token[-10:]}")
    logger.info(f"Token length: {len(token)}")
    
    if not os.path.exists(USER_DATA_ROOT):
        logger.error(f"USER_DATA_ROOT directory does not exist:")
        logger.error(f"  Relative path: {USER_DATA_ROOT}")
        logger.error(f"  Absolute path: {abs_user_data_root}")
        logger.error(f"  Exists check: {os.path.exists(abs_user_data_root)}")
        raise ValueError("User data directory not found")
    
    users_found = 0
    tokens_checked = 0
    
    try:
        user_dirs = os.listdir(USER_DATA_ROOT)
        logger.info(f"Found {len(user_dirs)} potential user directories: {user_dirs}")
    except Exception as e:
        logger.error(f"Error listing USER_DATA_ROOT: {e}")
        raise ValueError("Error accessing user data")
    
    for username in user_dirs:
        user_dir = os.path.join(USER_DATA_ROOT, username)
        abs_user_dir = os.path.abspath(user_dir)
        logger.info(f"Checking user directory: {user_dir} (absolute: {abs_user_dir})")
        
        if not os.path.isdir(user_dir):
            logger.debug(f"Skipping {username} - not a directory")
            continue
            
        users_found += 1
        
        # List all files in this user directory
        try:
            user_files = os.listdir(user_dir)
            logger.info(f"Files in user '{username}' directory: {user_files}")
        except Exception as e:
            logger.error(f"Error listing files in user directory {username}: {e}")
            continue
        
        reset_file_path = os.path.join(user_dir, "password_reset.json")
        abs_reset_file_path = os.path.abspath(reset_file_path)
        logger.info(f"Looking for reset file: {reset_file_path} (absolute: {abs_reset_file_path})")
        logger.info(f"Reset file exists: {os.path.exists(reset_file_path)}")

        if not os.path.exists(reset_file_path):
            logger.info(f"No reset file found for user {username} - skipping")
            continue

        logger.info(f"Found reset file for user {username}, reading token data")
        
        try:
            with open(reset_file_path, 'r') as f:
                reset_data_dict = json.load(f)
                logger.info(f"Reset file contents for {username}: {reset_data_dict}")
                reset_data = PasswordResetToken(**reset_data_dict)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error(f"Error parsing reset file for {username}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error reading reset file for {username}: {e}")
            continue

        tokens_checked += 1
        stored_token = reset_data.token
        logger.info(f"Comparing tokens for user {username}:")
        logger.info(f"  Provided token: '{token[:10]}...{token[-10:]}' (length: {len(token)})")
        logger.info(f"  Stored token:   '{stored_token[:10]}...{stored_token[-10:]}' (length: {len(stored_token)})")
        logger.info(f"  Tokens match: {stored_token == token}")
        
        # Also check for URL encoding issues
        import urllib.parse
        decoded_token = urllib.parse.unquote(token)
        logger.info(f"  URL decoded token: '{decoded_token[:10]}...{decoded_token[-10:]}' (length: {len(decoded_token)})")
        logger.info(f"  Decoded tokens match: {stored_token == decoded_token}")
        
        if reset_data.token == token or reset_data.token == decoded_token:
            logger.info(f"Token match found for user {username}!")
            matched_token = token if reset_data.token == token else decoded_token
            logger.info(f"Matched using {'original' if matched_token == token else 'URL-decoded'} token")
            
            # Check expiration
            try:
                expires_at = datetime.fromisoformat(reset_data.expires_at)
                current_time = datetime.utcnow()
                logger.info(f"Token expires at: {expires_at}")
                logger.info(f"Current time: {current_time}")
                logger.info(f"Token expired: {expires_at < current_time}")
                
                if expires_at < current_time:
                    logger.warning(f"Token expired for user {username}, removing reset file")
                    os.remove(reset_file_path)
                    raise ValueError("Password reset token has expired.")
            except ValueError as e:
                if "expired" in str(e):
                    raise
                logger.error(f"Error parsing expiration date for {username}: {e}")
                continue

            # Update password
            auth_file_path = os.path.join(user_dir, "auth.json")
            abs_auth_file_path = os.path.abspath(auth_file_path)
            logger.info(f"Updating password for user {username}")
            logger.info(f"Auth file: {auth_file_path} (absolute: {abs_auth_file_path})")
            
            if not os.path.exists(auth_file_path):
                logger.error(f"Auth file not found for user {username}: {auth_file_path}")
                os.remove(reset_file_path)
                raise FileNotFoundError("User auth file not found.")

            try:
                with open(auth_file_path, 'r+') as auth_file:
                    auth_data_dict = json.load(auth_file)
                    auth_data = UserAuth(**auth_data_dict)

                    new_password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    auth_data.password_hash = new_password_hash
                    logger.info(f"Password hash updated for user {username}")

                    if reset_data.is_admin_reset and 'admin' not in auth_data.roles:
                        auth_data.roles.append('admin')
                        logger.info(f"Added admin role to user {username}")

                    auth_file.seek(0)
                    json.dump(auth_data.dict(), auth_file, indent=2, default=str)
                    auth_file.truncate()
                    logger.info(f"Auth file updated for user {username}")

                os.remove(reset_file_path)
                logger.info(f"Reset token file removed for user {username}")
                logger.info(f"Password reset completed successfully for user {username}")
                return True
                
            except Exception as e:
                logger.error(f"Error updating auth file for user {username}: {e}")
                raise ValueError(f"Error updating user authentication: {e}")

    logger.warning(f"=== TOKEN NOT FOUND ===")
    logger.warning(f"Token not found after checking {users_found} users and {tokens_checked} tokens")
    logger.warning(f"Provided token: '{token}'")
    logger.warning(f"Current working directory: {cwd}")
    logger.warning(f"Searched in: {abs_user_data_root}")
    raise ValueError("Invalid password reset token.")
