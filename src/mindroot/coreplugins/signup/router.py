from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from lib.route_decorators import public_route, add_public_static
from lib.templates import render
from lib.providers.services import service_manager
from mindroot.coreplugins.user_service.models import UserCreate
from fastapi import Form
from typing import Optional
import os

router = APIRouter()

@router.get("/signup", response_class=HTMLResponse)
@public_route()
async def signup_page(request: Request, error: Optional[str] = None):
    return await render('signup', {
        "request": request,
        "error": error
    })

add_public_static( "/signup/static/")

@router.post("/signup")
@public_route()
async def handle_signup(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...)
):
    # Verify passwords match
    if password != password_confirm:
        return RedirectResponse(
            url=f"/signup?error=Passwords+do+not+match",
            status_code=303
        )
    
    try:
        # Create user data model
        user_data = UserCreate(
            username=username,
            email=email,
            password=password
        )
        
        # Get user service and create user
        await service_manager.create_user(user_data)
        
        # Redirect to login with verification message
        return RedirectResponse(
            url="/login?message=Account+created+successfully.+Please+check+your+email+to+verify+your+account.",
            status_code=303
        )
        
    except ValueError as e:
        # Handle validation errors
        return RedirectResponse(
            url=f"/signup?error={str(e)}",
            status_code=303
        )
    except Exception as e:
        # Handle unexpected errors
        print(f"Error in signup: {e}")
        return RedirectResponse(
            url=f"/signup?error=An+unexpected+error+occurred",
            status_code=303
        )

@router.get("/verify-email")
@public_route()
async def verify_email(token: str):
    try:
        if await service_manager.verify_email(token):
            return RedirectResponse(
                url="/login?message=Email+verified+successfully.+You+can+now+log+in.",
                status_code=303
            )
        return RedirectResponse(
            url="/login?error=Invalid+or+expired+verification+link",
            status_code=303
        )
    except Exception as e:
        print(f"Error in email verification: {e}")
        return RedirectResponse(
            url="/login?error=An+unexpected+error+occurred",
            status_code=303
        )
