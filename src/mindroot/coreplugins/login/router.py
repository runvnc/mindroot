from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from lib.route_decorators import public_route
from lib.templates import render
import os

router = APIRouter()

this_path = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(this_path, "templates"))


@router.get("/login", response_class=HTMLResponse)
@public_route()
async def login_page(request: Request):
    html = await render('login', {"request": request })
    return html

