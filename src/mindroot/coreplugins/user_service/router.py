from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.templates import render
from pydantic import BaseModel
import os
import json
import logging
import secrets
from .password_reset_service import reset_password_with_token, initiate_password_reset
from .mod import create_user
from .models import UserCreate
from typing import List, Optional
from lib.auth.api_key import verify_api_key
from lib.providers.services import service_manager
from lib.providers import ProviderManager
from lib.route_decorators import public_route
logger = logging.getLogger(__name__)
router = APIRouter()

def _is_trusted_source(request: Request) -> bool:
    """Check if request comes from localhost or Docker bridge gateway."""
    client_host = request.client.host if request.client else ""
    is_localhost = client_host in ("127.0.0.1", "::1", "localhost")
    if is_localhost:
        return True
    is_docker_gateway = False
    if client_host:
        parts = client_host.split(".")
        if len(parts) == 4:
            if parts[0] == "172" and parts[2] == "0" and parts[3] == "1":
                is_docker_gateway = True
    if not is_docker_gateway:
        real_ip = request.headers.get("X-Real-IP", "")
        if real_ip in ("127.0.0.1", "::1", "localhost"):
            is_docker_gateway = True
    is_trusted = is_localhost or is_docker_gateway
    logger.info(f"User API request from {client_host} (trusted={is_trusted})")
    return is_trusted

class APIUserCreate(BaseModel):
    """Request body for programmatic user creation (trusted sources only)."""
    username: str
    email: str
    password: Optional[str] = None
    roles: Optional[List[str]] = None

@public_route()
@router.post('/api/users/create')
async def api_create_user(request: Request, user_data: APIUserCreate):
    """Create a new user programmatically.

    Access control:
    - Requests from localhost or Docker bridge gateway are allowed without auth
      (for container bootstrap by mragent on the same host)
    - All other requests require authentication (Bearer token or session user)
    """
    if not _is_trusted_source(request):
        # Require authentication for non-trusted requests
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_data_auth = await verify_api_key(auth_header[7:])
            if not user_data_auth:
                raise HTTPException(status_code=401, detail="Invalid API key")
        elif not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Generate password if not provided
        import secrets as _secrets
        password = user_data.password or _secrets.token_urlsafe(16)
        roles = user_data.roles or ['user', 'verified']
        if 'user' not in roles:
            roles.append('user')

        create_data = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=password
        )
        result = await create_user(create_data, roles=roles, skip_verification=True)
        return {"success": True, "data": {"username": result.username, "email": result.email, "roles": roles}}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating user via API: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@public_route()
@router.get('/reset-password/{filename}')
async def get_reset_password_form_by_file(request: Request, filename: str):
    """Show password reset form if trigger file exists"""
    trigger_dir = 'data/password_resets'
    file_path = os.path.join(trigger_dir, f'{filename}')
    if not filename or not filename.replace('-', '').replace('_', '').isalnum():
        html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Invalid file format', 'success': False})
        return HTMLResponse(content=html)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Reset file not found or expired', 'success': False})
        return HTMLResponse(content=html)
    html = await render('reset_password', {'request': request, 'token': filename, 'error': None, 'success': False})
    return HTMLResponse(content=html)

@public_route()
@router.post('/reset-password/{filename}')
async def handle_reset_password_by_file(request: Request, filename: str, password: str=Form(...), confirm_password: str=Form(...), services: ProviderManager=Depends(lambda: service_manager)):
    """Handle password reset using trigger file"""
    trigger_dir = 'data/password_resets'
    file_path = os.path.join(trigger_dir, f'{filename}')
    if not filename or not filename.replace('-', '').replace('_', '').isalnum():
        html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Invalid file format', 'success': False})
        return HTMLResponse(content=html)
    if password != confirm_password:
        html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Passwords do not match.', 'success': False})
        return HTMLResponse(content=html)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Reset file not found or expired.', 'success': False})
        return HTMLResponse(content=html)
    try:
        with open(file_path, 'r') as f:
            data = f.read().strip()
        parts = data.split(' ')
        if len(parts) != 2:
            html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Invalid reset file format.', 'success': False})
            return HTMLResponse(content=html)
        username, is_admin_reset_str = parts
        is_admin_reset = is_admin_reset_str.lower() == 'true'
        if not username:
            html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Invalid reset file format.', 'success': False})
            return HTMLResponse(content=html)
        logger.info(f'Processing password reset for user: {username} from file: {filename}')
        token = await initiate_password_reset(username=username, is_admin_reset=is_admin_reset)
        success = await reset_password_with_token(token=token, new_password=password)
        if success:
            os.remove(file_path)
            logger.info(f'Successfully reset password for {username}, removed trigger file: {filename}')
            html = await render('reset_password', {'request': request, 'token': filename, 'error': None, 'success': True})
            return HTMLResponse(content=html)
        else:
            html = await render('reset_password', {'request': request, 'token': filename, 'error': 'Password reset failed.', 'success': False})
            return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f'Error processing trigger file {filename}: {e}')
        html = await render('reset_password', {'request': request, 'token': filename, 'error': f'Error processing reset: {str(e)}', 'success': False})
        return HTMLResponse(content=html)
