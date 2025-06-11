from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.templates import render
import os
import json
import logging
# Import services directly to avoid coroutine-call confusion
from .password_reset_service import reset_password_with_token, initiate_password_reset
from lib.providers.services import service_manager
from lib.providers import ProviderManager
from lib.route_decorators import public_route

logger = logging.getLogger(__name__)
router = APIRouter()

@public_route()
@router.get("/reset-password/{filename}")
async def get_reset_password_form_by_file(request: Request, filename: str):
    """Show password reset form if trigger file exists"""
    trigger_dir = "data/password_resets"
    file_path = os.path.join(trigger_dir, f"{filename}.json")
    
    if not filename or len(filename) < 10:  # Basic validation for token-like filename
        html = await render('reset_password', {"request": request, "token": filename, "error": "Invalid file format", "success": False})
        return HTMLResponse(content=html)
    
    if not os.path.exists(file_path):
        html = await render('reset_password', {"request": request, "token": filename, "error": "Reset file not found or expired", "success": False})
        return HTMLResponse(content=html)
    
    # File exists, show the form
    html = await render('reset_password', {"request": request, "token": filename, "error": None, "success": False})
    return HTMLResponse(content=html)

@public_route()
@router.post("/reset-password/{filename}")
async def handle_reset_password_by_file(request: Request, filename: str, password: str = Form(...), confirm_password: str = Form(...), services: ProviderManager = Depends(lambda: service_manager)):
    """Handle password reset using trigger file"""
    trigger_dir = "data/password_resets"
    file_path = os.path.join(trigger_dir, f"{filename}.json")
    
    if password != confirm_password:
        html = await render('reset_password', {"request": request, "token": filename, "error": "Passwords do not match.", "success": False})
        return HTMLResponse(content=html)
    
    if not os.path.exists(file_path):
        html = await render('reset_password', {"request": request, "token": filename, "error": "Reset file not found or expired.", "success": False})
        return HTMLResponse(content=html)
    
    try:
        # Read the trigger file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        username = data.get("username")
        is_admin_reset = data.get("is_admin_reset", False)
        
        if not username:
            html = await render('reset_password', {"request": request, "token": filename, "error": "Invalid reset file format.", "success": False})
            return HTMLResponse(content=html)
        
        logger.info(f"Processing password reset for user: {username} from file: {filename}")
        
        # Generate token and reset password
        token = await services.get('user_service.initiate_password_reset')(username=username, is_admin_reset=is_admin_reset)
        success = await services.get('user_service.reset_password_with_token')(token=token, new_password=password)
        
        if success:
            # Delete the trigger file
            os.remove(file_path)
            logger.info(f"Successfully reset password for {username}, removed trigger file: {filename}")
            html = await render('reset_password', {"request": request, "token": filename, "error": None, "success": True})
            return HTMLResponse(content=html)
        else:
            html = await render('reset_password', {"request": request, "token": filename, "error": "Password reset failed.", "success": False})
            return HTMLResponse(content=html)
            
    except Exception as e:
        logger.error(f"Error processing trigger file {filename}: {e}")
        html = await render('reset_password', {"request": request, "token": filename, "error": f"Error processing reset: {str(e)}", "success": False})
        return HTMLResponse(content=html)
