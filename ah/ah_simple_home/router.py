from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter()
templates = Jinja2Templates(directory="ah/ah_simple_home/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    agents = [agent for agent in os.listdir("data/agents/local") if os.path.isdir(os.path.join("data/agents/local", agent))]
    return templates.TemplateResponse("home.jinja2", {"request": request, "agents": agents})

@router.get("/admin")
async def admin():
    return RedirectResponse("/admin")

@router.get("/{agent_name}", response_class=HTMLResponse)
async def agent_page(request: Request, agent_name: str):
    agent_dir = os.path.join("data/agents/local", agent_name)
    if os.path.isdir(agent_dir):
        return templates.TemplateResponse("agent.jinja2", {"request": request, "agent_name": agent_name})
    else:
        return HTMLResponse(f"Agent '{agent_name}' not found.")
