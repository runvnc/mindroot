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
    
    # Get agent data with persona information
    agents_with_personas = []
    for agent_name in agent_dirs:
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
    
    # Try to sort agents by last access time
    agent_access_times = []
    chatlog_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
    for agent in agent_dirs:
        # Look for the most recent log file for this agent
        # Search across all user directories for this agent's logs
        log_pattern = f"{chatlog_dir}/*/{agent}/chatlog_*.json"
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
    html = await render('home', {"user": user, "request": request, "agents": agents, "agents_with_personas": agents_with_personas })
    return HTMLResponse(html)
