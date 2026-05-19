from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.templates import render
import os
import json
import logging
import secrets
from .password_reset_service import reset_password_with_token, initiate_password_reset
from .mod import create_user
from .models import UserCreate
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
