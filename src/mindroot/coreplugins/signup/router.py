from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.route_decorators import public_route
from lib.templates import render
from lib.providers.services import service_manager
from mindroot.coreplugins.user_service.models import UserCreate
from fastapi import Form
from typing import Optional

router = APIRouter()

@router.get("/signup", response_class=HTMLResponse)
@public_route()
async def signup_page(request: Request, error: Optional[str] = None):
    return await render('signup', {
        "request": request,
        "error": error
    })

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
        
        # Redirect to login
        return RedirectResponse(
            url="/login?message=Account+created+successfully",
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
