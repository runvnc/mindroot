from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pathlib import Path
import json
from .agent_importer import scan_and_import_agents, import_github_agent

router = APIRouter()

BASE_DIR = Path('data/agents')
local_dir = BASE_DIR / "local"
shared_dir = BASE_DIR / "shared"
local_dir.mkdir(parents=True, exist_ok=True)
shared_dir.mkdir(parents=True, exist_ok=True)

class GitHubImportRequest(BaseModel):
    repo_path: str  # Format: "owner/repo"
    scope: str
    tag: str = None

@router.get('/agents/{scope}/{name}')
def read_agent(scope: str, name: str):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    agent_path = BASE_DIR / scope / name / 'agent.json'
    if not agent_path.exists():
        raise HTTPException(status_code=404, detail='Agent not found')
    with open(agent_path, 'r') as f:
        agent = json.load(f)
    return agent

@router.get('/agents/{scope}')
def list_agents(scope: str):
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    scope_dir = BASE_DIR / scope
    agents = [p.name for p in scope_dir.iterdir() if p.is_dir()]
    return [{'name': name} for name in agents]

@router.post('/agents/{scope}')
def create_agent(scope: str, agent: str = Form(...)):
    try:
        agent = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        agent_name = agent.get('name')
        if not agent_name:
            raise HTTPException(status_code=400, detail='Agent name is required')
        agent_path = BASE_DIR / scope / agent_name / 'agent.json'
        if agent_path.exists():
            raise HTTPException(status_code=400, detail='Agent already exists')
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        with open(agent_path, 'w') as f:
            json.dump(agent, f, indent=2)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e))

@router.put('/agents/{scope}/{name}')
def update_agent(scope: str, name: str, agent: str = Form(...)):
    try:
        agent = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
        agent_path = BASE_DIR / scope / name / 'agent.json'
        if not agent_path.exists():
            raise HTTPException(status_code=404, detail='Agent not found')
        with open(agent_path, 'w') as f:
            json.dump(agent, f, indent=2)
        return {'status': 'success'}
    except Exception as e:
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e))

class ScanDirectoryRequest(BaseModel):
    directory: str
    scope: str

@router.post('/scan-and-import-agents')
def scan_and_import_agents_endpoint(request: ScanDirectoryRequest):
    try:
        result = scan_and_import_agents(Path(request.directory), request.scope)
        return {
            'success': True,
            'message': f"Imported {result['total_imported']} out of {result['total_discovered']} discovered agents",
            'imported_agents': result['imported_agents']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during import: {str(e)}")

@router.post('/import-github-agent')
def import_github_agent_endpoint(request: GitHubImportRequest):
    try:
        if request.scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')

        result = import_github_agent(request.repo_path, request.scope, request.tag)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['message'])
            
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during GitHub import: {str(e)}")
