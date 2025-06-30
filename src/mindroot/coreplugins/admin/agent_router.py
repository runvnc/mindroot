from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import json
from .agent_importer import scan_and_import_agents, import_github_agent
from lib.providers.commands import command_manager
from .persona_handler import handle_persona_import, import_persona_from_index
import traceback
import hashlib
import zipfile
import io
import tempfile
import time
from typing import Dict, Any
from datetime import datetime

router = APIRouter()

BASE_DIR = Path('data/agents')
local_dir = BASE_DIR / "local"
shared_dir = BASE_DIR / "shared"
local_dir.mkdir(parents=True, exist_ok=True)
shared_dir.mkdir(parents=True, exist_ok=True)

# Cache for agent ownership info
_agent_ownership_cache = None
_cache_timestamp = 0

class GitHubImportRequest(BaseModel):
    repo_path: str  # Format: "owner/repo"
    scope: str
    tag: str = None

def scan_agent_ownership() -> Dict[str, Any]:
    """Scan all agents and build ownership information"""
    ownership_info = {
        'agents': {},
        'scanned_at': datetime.now().isoformat(),
        'total_agents': 0,
        'owned_agents': 0,
        'external_agents': 0
    }
    
    # Scan both local and shared directories
    for scope in ['local', 'shared']:
        scope_dir = BASE_DIR / scope
        if not scope_dir.exists():
            continue
            
        for agent_dir in scope_dir.iterdir():
            if not agent_dir.is_dir():
                continue
               
            agent_json_path = agent_dir / 'agent.json'
            if not agent_json_path.exists():
                continue
                
            try:
                with open(agent_json_path, 'r') as f:
                    agent_data = json.load(f)
                
                agent_name = agent_data.get('name', agent_dir.name)
                
                # Extract ownership information
                creator = agent_data.get('creator')
                owner = agent_data.get('owner')
                registry_owner = agent_data.get('registry_owner')
                created_by = agent_data.get('created_by')
                
                # Determine if this agent has external ownership
                has_external_owner = bool(creator or owner or registry_owner or created_by)
                
                ownership_info['agents'][f"{scope}/{agent_name}"] = {
                    'name': agent_name,
                    'scope': scope,
                    'creator': creator,
                    'owner': owner,
                    'registry_owner': registry_owner,
                    'created_by': created_by,
                    'has_external_owner': has_external_owner,
                    'description': agent_data.get('description', ''),
                    'version': agent_data.get('version', '1.0.0')
                }
                
                ownership_info['total_agents'] += 1
                if has_external_owner:
                    ownership_info['external_agents'] += 1
                else:
                    ownership_info['owned_agents'] += 1
                    
            except Exception as e:
                print(f"Error reading agent {agent_dir.name}: {e}")
                continue
    
    return ownership_info

async def load_persona_data(persona_name: str) -> dict:
    """Load persona data from local or shared directory"""
    # Handle registry personas: registry/owner/name
    if persona_name.startswith('registry/'):
        persona_path = Path(f'personas/{persona_name}/persona.json')
        if persona_path.exists():
            with open(persona_path, 'r') as f:
                return json.load(f)
    
    # Fallback to existing local/shared pattern (UNCHANGED)
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

@router.get('/command-providers')
def get_command_providers():
    """Get all available providers for each command"""
    result = {}
    for command_name, providers in command_manager.functions.items():
        result[command_name] = [
            p['provider'] for p in providers
        ]
    return result

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
    agents = []
    for p in scope_dir.iterdir():
        if p.is_dir():
            agent_json_path = p / 'agent.json'
            if agent_json_path.exists():
                try:
                    with open(agent_json_path, 'r') as f:
                        agent_data = json.load(f)
                    agents.append(agent_data)
                except Exception as e:
                    # If we can't read the agent.json, just include the name
                    agents.append({'name': p.name})
    return agents

@router.get('/agents/ownership-info')
def get_agent_ownership_info():
    """Get cached ownership information for all agents"""
    global _agent_ownership_cache, _cache_timestamp
    
    # Cache for 5 minutes
    cache_duration = 300  # 5 minutes in seconds
    current_time = time.time()
    
    if (_agent_ownership_cache is None or 
        current_time - _cache_timestamp > cache_duration):
        
        _agent_ownership_cache = scan_agent_ownership()
        _cache_timestamp = current_time
    
    return _agent_ownership_cache

@router.post('/agents/refresh-ownership-cache')
def refresh_agent_ownership_cache():
    """Force refresh of the agent ownership cache"""
    global _agent_ownership_cache, _cache_timestamp
    
    _agent_ownership_cache = scan_agent_ownership()
    _cache_timestamp = time.time()
    
    return {
        'success': True,
        'message': 'Agent ownership cache refreshed',
        'data': _agent_ownership_cache
    }

@router.post('/agents/{scope}')
def create_agent(scope: str, agent: str = Form(...)):
    try:
        print(f"Creating agent in scope: {scope}")
        agent_data = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
       
        agent_name = agent_data.get('name')
        if not agent_name:
            raise HTTPException(status_code=400, detail='Agent name is required')

        print(f"Agent name: {agent_name}")
        if "indexName" in agent_data and agent_data["indexName"] is not None:
            print("Import agent from index: " + agent_data["indexName"])
            import_persona_from_index(agent_data["indexName"], agent_data['persona'])

        if 'persona' in agent_data:
            # This will either return the persona name or handle the import
            # and return the name
            # Extract owner information for registry personas
            owner = agent_data.get('registry_owner') or agent_data.get('owner') or agent_data.get('creator')
            persona_scope = 'registry' if owner else scope
            
            persona_name = handle_persona_import(agent_data['persona'], persona_scope, owner)
            
            agent_data['persona'] = persona_name
        
        # Ensure recommended_plugins is present and is a list (also handle legacy required_plugins)
        if 'required_plugins' not in agent_data:
            agent_data['required_plugins'] = []
        elif not isinstance(agent_data['required_plugins'], list):
            agent_data['required_plugins'] = list(agent_data['required_plugins'])
            
        # Ensure preferred_providers is present and is a list
        if 'preferred_providers' not in agent_data:
            agent_data['recommended_plugins'] = []
        elif not isinstance(agent_data['recommended_plugins'], list):
            agent_data['recommended_plugins'] = list(agent_data['recommended_plugins'])
            
        # Ensure preferred_providers is present and is a list
        if 'preferred_providers' not in agent_data:
            agent_data['preferred_providers'] = []
        elif not isinstance(agent_data['preferred_providers'], list):
            agent_data['preferred_providers'] = list(agent_data['preferred_providers'])
            
        agent_path = BASE_DIR / scope / agent_name / 'agent.json'
        if agent_path.exists():
            # Check if overwrite parameter is provided
            overwrite = agent_data.get('overwrite', False)
            if not overwrite:
                raise HTTPException(status_code=400, detail='Agent already exists')
            else:
                # If overwrite is True, we'll proceed to overwrite the existing agent
                print(f"Overwriting existing agent: {agent_name}")
            
        print(f"Creating agent directory: {agent_path.parent}")
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Writing agent file: {agent_path}")
        with open(agent_path, 'w') as f:
            json.dump(agent_data, f, indent=2)
            
        print(f"Successfully created agent: {agent_name}")
        return {'status': 'success'}
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error creating agent: {str(e)}\n{trace}")
        raise HTTPException(status_code=500, detail=f'Internal server error: {str(e)}\nTrace: {trace}')
@router.put('/agents/{scope}/{name}')
def update_agent(scope: str, name: str, agent: str = Form(...)):
    try:
        agent = json.loads(agent)
        if scope not in ['local', 'shared']:
            raise HTTPException(status_code=400, detail='Invalid scope')
            
        # Ensure recommended_plugins is present and is a list (also handle legacy required_plugins)
        if 'required_plugins' not in agent:
            agent['required_plugins'] = []
        elif not isinstance(agent['required_plugins'], list):
            agent['required_plugins'] = list(agent['required_plugins'])
            
        # Ensure recommended_plugins is present and is a list
        if 'recommended_plugins' not in agent:
            agent['required_plugins'] = []
        elif not isinstance(agent['required_plugins'], list):
            agent['required_plugins'] = list(agent['required_plugins'])
            
        if 'preferred_providers' not in agent:
            agent['preferred_providers'] = []
        elif not isinstance(agent['preferred_providers'], list):
            agent['preferred_providers'] = list(agent['preferred_providers'])
            
        agent_path = BASE_DIR / scope / name / 'agent.json'
        without_hash = agent.copy()
        without_hash.pop('hashver', None)  # Remove the hash if it exists

        consistent_json = json.dumps(without_hash, sort_keys=True, separators=(',', ':'))
        hashver = hashlib.sha256(consistent_json.encode('utf-8')).hexdigest()[:4]
      
        agent['hashver'] = hashver

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

@router.get('/agents/{scope}/{name}/export')
def export_agent_zip(scope: str, name: str):
    """Export an agent as a zip file"""
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    
    agent_dir = BASE_DIR / scope / name
    if not agent_dir.exists():
        raise HTTPException(status_code=404, detail='Agent not found')
    
    try:
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add all files from the agent directory
            for file_path in agent_dir.rglob('*'):
                if file_path.is_file():
                    # Use relative path within the zip
                    arcname = file_path.relative_to(agent_dir)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type='application/zip',
            headers={'Content-Disposition': f'attachment; filename="{name}_agent.zip"'}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating zip: {str(e)}")

@router.post('/agents/{scope}/import-zip')
async def import_agent_zip(scope: str, file: UploadFile = File(...)):
    """Import an agent from a zip file"""
    if scope not in ['local', 'shared']:
        raise HTTPException(status_code=400, detail='Invalid scope')
    
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail='File must be a zip file')
    
    try:
        # Read the uploaded file
        content = await file.read()
        
        # Create a temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract zip file
            with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_file:
                zip_file.extractall(temp_path)
            
            # Find agent.json file
            agent_json_files = list(temp_path.rglob('agent.json'))
            if not agent_json_files:
                raise HTTPException(status_code=400, detail='No agent.json found in zip file')
            
            agent_json_path = agent_json_files[0]
            
            # Load agent data
            with open(agent_json_path, 'r') as f:
                agent_data = json.load(f)
            
            agent_name = agent_data.get('name')
            if not agent_name:
                raise HTTPException(status_code=400, detail='Agent name not found in agent.json')
            
            # Check if agent already exists
            target_dir = BASE_DIR / scope / agent_name
            if target_dir.exists():
                # For zip imports, we could add overwrite support in the future
                # For now, we'll keep the existing behavior but make the error message consistent
                raise HTTPException(
                    status_code=400, 
                    detail=f'Agent {agent_name} already exists. Use the registry manager for updates.'
                )
            
            # Copy extracted files to target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Get the directory containing agent.json
            source_dir = agent_json_path.parent
            
            # Copy all files from source to target
            import shutil
            for item in source_dir.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(source_dir)
                    target_file = target_dir / relative_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_file)
        
        return {
            'success': True,
            'message': f'Agent {agent_name} imported successfully',
            'agent_name': agent_name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing zip: {str(e)}")
