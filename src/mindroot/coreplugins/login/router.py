from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.route_decorators import public_route
from lib.templates import render
from lib.providers.services import service_manager
from mindroot.coreplugins.jwt_auth.middleware import create_access_token
from typing import Optional
import os

router = APIRouter()
REQUIRE_EMAIL_VERIFY = os.environ.get('REQUIRE_EMAIL_VERIFY', '').lower() == 'true'

@router.get("/login", response_class=HTMLResponse)
@public_route()
async def login_page(request: Request, error: Optional[str] = None, message: Optional[str] = None):
    return await render('login', {
        "request": request,
        "error": error,
        "message": message
    })

@router.post("/login")
@public_route()
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        # First verify credentials
        if await service_manager.verify_user(username, password):
            # Get user data
            user_data = await service_manager.get_user_data(username)
            
            if user_data:
                # Check if email verification is required and not verified
                if REQUIRE_EMAIL_VERIFY and not user_data.email_verified:
                    return RedirectResponse(
                        url="/login?error=Please+verify+your+email+before+logging+in",
                        status_code=303
                    )
                
                # Create access token
                access_token = create_access_token(data={"sub": username, **user_data.dict()})
                
                # Create response with redirect
                response = RedirectResponse(url="/", status_code=303)
                
                # Set cookie
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    max_age=604800,  # 1 week
                    httponly=True,   # Prevent JavaScript access
                    samesite="Lax"  # CSRF protection
                )
                
                return response
            
        # If we get here, authentication failed
        return RedirectResponse(
            url="/login?error=Invalid+username+or+password",
            status_code=303
        )
        
    except Exception as e:
        print(f"Login error: {e}")
        return RedirectResponse(
            url="/login?error=An+unexpected+error+occurred",
            status_code=303
        )

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
