from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from lib.templates import render
from lib.route_decorators import add_public_static
import os
import glob
from datetime import datetime
import time

router = APIRouter()

add_public_static('/home/static/')

#this_path = os.path.dirname(os.path.realpath(__file__))
#templates = Jinja2Templates(directory=os.path.join(this_path, "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get all agent directories
    agent_dirs = [agent for agent in os.listdir("data/agents/local") if os.path.isdir(os.path.join("data/agents/local", agent))]
    
    # Try to sort agents by last access time
    agent_access_times = []
    for agent in agent_dirs:
        # Look for the most recent log file for this agent
        log_pattern = f"data/chatlogs/{agent}_*.json"
        log_files = glob.glob(log_pattern)
        
        if log_files:
            # Get the most recent log file's modification time
            latest_log = max(log_files, key=os.path.getmtime)
            mtime = os.path.getmtime(latest_log)
        else:
            # If no logs, use the agent.json file's modification time
            agent_file = os.path.join("data/agents/local", agent, "agent.json")
            if os.path.exists(agent_file):
                mtime = os.path.getmtime(agent_file)
            else:
                mtime = 0  # Default to oldest if no file found
        
        agent_access_times.append((agent, mtime))
    
    # Sort by modification time (most recent first)
    agent_access_times.sort(key=lambda x: x[1], reverse=True)
    
    # Extract just the agent names in sorted order
    agents = [agent for agent, _ in agent_access_times]
    
    user = request.state.user
    html = await render('home', {"user": user, "request": request, "agents": agents })
    return HTMLResponse(html)
