from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from lib.templates import render
from lib.route_decorators import add_public_static
import os
import glob
import json
from lib.providers.services import service_manager
from datetime import datetime
from pathlib import Path
import time

router = APIRouter()

add_public_static('/home/static/')

#this_path = os.path.dirname(os.path.realpath(__file__))
#templates = Jinja2Templates(directory=os.path.join(this_path, "templates"))

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # Get all agent directories
    agent_dirs = []
    
    # Check local agents
    if os.path.exists("data/agents/local"):
        agent_dirs.extend([agent for agent in os.listdir("data/agents/local") if os.path.isdir(os.path.join("data/agents/local", agent))])
    
    # Check shared agents
    if os.path.exists("data/agents/shared"):
        shared_agents = [agent for agent in os.listdir("data/agents/shared") if os.path.isdir(os.path.join("data/agents/shared", agent))]
        agent_dirs.extend(shared_agents)
    
    # Sort agents by last usage time using marker files
    agent_access_times = []
    for agent in agent_dirs:
        # Check for .last_used marker file
        marker_path = Path(f"data/agents/local/{agent}/.last_used")
        if not marker_path.exists():
            marker_path = Path(f"data/agents/shared/{agent}/.last_used")
        
        if marker_path.exists():
            last_used = marker_path.stat().st_mtime
        else:
            # If no marker exists, fall back to agent.json modification time
            agent_file = os.path.join("data/agents/local", agent, "agent.json")
            if not os.path.exists(agent_file):
                agent_file = os.path.join("data/agents/shared", agent, "agent.json")
            if os.path.exists(agent_file):
                last_used = os.path.getmtime(agent_file)
            else:
                last_used = 0  # Default to oldest if no file found
        
        agent_access_times.append((agent, last_used))
    
    # Sort by last used time (most recent first)
    agent_access_times.sort(key=lambda x: x[1], reverse=True)
    
    # Extract just the agent names in sorted order
    agents = [agent for agent, _ in agent_access_times]
    
    # Get agent data with persona information in sorted order
    agents_with_personas = []
    for agent_name in agents:
        try:
            agent_data = await service_manager.get_agent_data(agent_name)
            # Get the original persona reference from the agent.json file directly
            # to preserve registry paths like "registry/owner/name"
            agent_file_path = f"data/agents/local/{agent_name}/agent.json"
            if not os.path.exists(agent_file_path):
                agent_file_path = f"data/agents/shared/{agent_name}/agent.json"
            
            with open(agent_file_path, 'r') as f:
                raw_agent_data = json.load(f)
            persona_path = raw_agent_data.get('persona', agent_name)
            
            agents_with_personas.append({
                'name': agent_name,
                'persona': persona_path,
                'agent_data': agent_data  # Include full agent data for template
            })
        except Exception as e:
            # Fallback if agent data can't be loaded
            agents_with_personas.append({'name': agent_name, 'persona': agent_name})
    
    user = request.state.user
    html = await render('home', {"user": user, "request": request, "agents": agents, "agents_with_personas": agents_with_personas })
    return HTMLResponse(html)
