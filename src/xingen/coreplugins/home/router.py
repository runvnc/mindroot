from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()

this_path = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(this_path, "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    agents = [agent for agent in os.listdir("data/agents/local") if os.path.isdir(os.path.join("data/agents/local", agent))]
    return templates.TemplateResponse("home.jinja2", {"request": request, "agents": agents})


