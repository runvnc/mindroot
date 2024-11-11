from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from lib.templates import render
import os

router = APIRouter()

this_path = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(this_path, "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    agents = [agent for agent in os.listdir("data/agents/local") if os.path.isdir(os.path.join("data/agents/local", agent))]
    user = request.state.user
    html = await render('home', {"user": user, "request": request, "agents": agents })
    return HTMLResponse(html)

