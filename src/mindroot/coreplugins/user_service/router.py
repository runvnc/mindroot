from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.templates import render
# Import services directly to avoid coroutine-call confusion
from .password_reset_service import reset_password_with_token, initiate_password_reset
from lib.providers.services import service_manager
from lib.providers import ProviderManager

router = APIRouter()

@router.get("/reset-password/{token}")
async def get_reset_password_form(request: Request, token: str):
    html = await render('reset_password', {"request": request, "token": token, "error": None, "success": False})
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

@router.post("/reset-password/{token}")
async def handle_reset_password(request: Request, token: str, password: str = Form(...), confirm_password: str = Form(...), services: ProviderManager = Depends(lambda: service_manager)):
    if password != confirm_password:
        html = await render('reset_password', {"request": request, "token": token, "error": "Passwords do not match.", "success": False})
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)

    try:
        # Direct call to the service function
        success = await reset_password_with_token(token=token, new_password=password)
        if success:
            html = await render('reset_password', {"request": request, "token": token, "error": None, "success": True})
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)
        else:
            html = await render('reset_password', {"request": request, "token": token, "error": "Invalid or expired token.", "success": False})
            from fastapi.responses import HTMLResponse
            return HTMLResponse(content=html)
    except ValueError as e:
        html = await render('reset_password', {"request": request, "token": token, "error": str(e), "success": False})
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html)

# This is an admin-only function to generate a reset link.
# In a real app, this would be more protected.
@router.get("/admin/initiate-reset/{username}")
async def admin_initiate_reset(username: str, services: ProviderManager = Depends(lambda: service_manager)):
    try:
        token = await services.get('user_service.initiate_password_reset')(username=username)
        return HTMLResponse(f'<h1>Password Reset Link</h1><p>Share this link with the user: <a href="/user_service/reset-password/{token}">/user_service/reset-password/{token}</a></p>')
    except ValueError as e:
        return HTMLResponse(f'<h1>Error</h1><p>{str(e)}</p>', status_code=404)
