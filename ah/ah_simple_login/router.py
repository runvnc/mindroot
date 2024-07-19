from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ah.route_decorators import public_route

router = APIRouter()
templates = Jinja2Templates(directory="ah/ah_simple_login/templates")

@public_route
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
