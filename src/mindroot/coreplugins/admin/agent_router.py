from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from pathlib import Path
import json
from .agent_importer import scan_and_import_agents, import_github_agent
from .persona_handler import handle_persona_import, import_persona_from_index
import traceback

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

async def load_persona_data(persona_name: str) -> dict:
    """Load persona data from local or shared directory"""
    persona_path = Path('personas/local') / persona_name / 'persona.json'
    if not persona_path.exists():
        persona_path = Path('personas/shared') / persona_name / 'persona.json'
        
    if not persona_path.exists():
        return {}
        
    with open(persona_path, 'r') as f:
        return json.load(f)

async def load_agent_data(agent_name: str) -> dict:
    """Load agent data from local or shared directory"""
    agent_path = BASE_DIR / 'local' / agent_name / 'agent.json'
    if not agent_path.exists():
        agent_path = BASE_DIR / 'shared' / agent_name / 'agent.json'
        if not agent_path.exists():
            raise FileNotFoundError(f'Agent {agent_name} not found')
    
    with open(agent_path, 'r') as f:
        agent_data = json.load(f)
        
    # Get the persona data if specified
    if 'persona' in agent_data:
        persona_data = await load_persona_data(agent_data['persona'])
        agent_data['persona'] = persona_data
        
    return agent_data

@router.get('/agents/full/{scope}/{name}')
async def get_full_agent_data(scope: str, name: str):
    """Get complete agent data including persona"""
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    
    try:
        agent_data = await load_agent_data(name)
        return agent_data
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
        agent_data = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')

       
        agent_name = agent_data.get('name')
        if not agent_name:
            raise HTTPException(status_code=400, detail='Agent name is required')

        if "indexName" in agent_data and agent_data["indexName"] is not None:
            print("Import agent from index: " + agent_data["indexName"])
            import_persona_from_index(agent_data["indexName"], agent_data['persona'])

        if 'persona' in agent_data:
            # This will either return the persona name or handle the import
            # and return the name
            persona_name = handle_persona_import(agent_data['persona'], scope)
 
            agent_data['persona'] = persona_name
            
        agent_path = BASE_DIR / scope / agent_name / 'agent.json'
        if agent_path.exists():
            raise HTTPException(status_code=400, detail='Agent already exists')
            
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        with open(agent_path, 'w') as f:
            json.dump(agent_data, f, indent=2)
            
        return {'status': 'success'}
    except Exception as e:
        trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail='Internal server error ' + str(e) + "\n" + trace)

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
