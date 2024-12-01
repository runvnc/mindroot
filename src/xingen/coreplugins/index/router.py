import json
import os
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from lib.plugins import load_plugin_manifest, save_plugin_manifest

router = APIRouter()

ORIGINAL_WORKING_DIR = os.getcwd()
INDEX_DIR = Path(ORIGINAL_WORKING_DIR) / 'indices'

# Ensure index directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

class IndexMetadata(BaseModel):
    name: str
    description: Optional[str] = ""
    version: str = "1.0.0"
    url: Optional[str] = None
    trusted: bool = False

class PluginEntry(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    source: str
    source_path: Optional[str] = None
    github_url: Optional[str] = None
    commands: List[str] = []
    services: List[str] = []
    dependencies: List[str] = []

class AgentEntry(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    required_commands: List[str] = []
    required_services: List[str] = []

async def load_persona_data(persona_name: str) -> dict:
    """Load persona data from local or shared directory"""
    try:
        persona_path = Path('personas/local') / persona_name / 'persona.json'
        if not persona_path.exists():
            persona_path = Path('personas/shared') / persona_name / 'persona.json'
            
        if not persona_path.exists():
            return {}
            
        with open(persona_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in persona file: {persona_name}")

async def load_agent_data(agent_name: str) -> dict:
    """Load agent data from local or shared directory"""
    try:
        agent_path = Path('data/agents/local') / agent_name / 'agent.json'
        if not agent_path.exists():
            agent_path = Path('data/agents/shared') / agent_name / 'agent.json'
            if not agent_path.exists():
                raise FileNotFoundError(f'Agent {agent_name} not found')
        
        with open(agent_path, 'r') as f:
            agent_data = json.load(f)
            
        # Validate required fields
        if 'name' not in agent_data:
            raise ValueError(f'Agent {agent_name} missing required field: name')
            
        # Get the persona data if specified
        if 'persona' in agent_data:
            persona_data = await load_persona_data(agent_data['persona'])
            agent_data['persona'] = persona_data
            
        return agent_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"Invalid JSON in agent file: {agent_name}")

@router.get("/index/list-indices")
async def list_indices():
    """List all available indices"""
    try:
        indices = []
        if not any(INDEX_DIR.glob('*.json')):
            this_script_path = Path(__file__).parent
            default_index_path = this_script_path / 'default.json'

            with open(default_index_path, 'r') as f:
                default_index_data = json.load(f)
                with open(INDEX_DIR / 'default.json', 'w') as f:
                    json.dump(default_index_data, f, indent=2)

        for file in INDEX_DIR.glob('*.json'):
            try:
                with open(file, 'r') as f:
                    index_data = json.load(f)
                    manifest = load_plugin_manifest()
                    index_data['installed'] = file.stem in manifest.get('indices', {}).get('installed', {})
                    indices.append(index_data)
            except json.JSONDecodeError:
                continue  # Skip invalid JSON files
        return JSONResponse({'success': True, 'data': indices})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/create-index")
async def create_index(metadata: IndexMetadata):
    """Create a new index"""
    try:
        file_path = INDEX_DIR / f"{metadata.name}.json"
        if file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index already exists'})

        index_data = {
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'url': metadata.url,
            'trusted': metadata.trusted,
            'created_at': datetime.now().isoformat(),
            'plugins': [],
            'agents': []
        }

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/update-index/{index_name}")
async def update_index(index_name: str, metadata: IndexMetadata):
    """Update index metadata"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        index_data.update({
            'name': metadata.name,
            'description': metadata.description,
            'version': metadata.version,
            'url': metadata.url,
            'trusted': metadata.trusted,
            'updated_at': datetime.now().isoformat()
        })

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/add-plugin/{index_name}")
async def add_plugin(index_name: str, plugin: PluginEntry):
    """Add a plugin to an index"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        if any(p['name'] == plugin.name for p in index_data['plugins']):
            return JSONResponse({'success': False, 'message': 'Plugin already in index'})

        plugin_data = {
            'name': plugin.name,
            'version': plugin.version,
            'description': plugin.description,
            'source': plugin.source,
            'source_path': plugin.source_path,
            'github_url': plugin.github_url,
            'commands': plugin.commands,
            'services': plugin.services,
            'dependencies': plugin.dependencies,
            'added_at': datetime.now().isoformat()
        }

        index_data['plugins'].append(plugin_data)

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/add-agent/{index_name}")
async def add_agent(index_name: str, agent: AgentEntry):
    """Add an agent to an index"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        try:
            agent_data = await load_agent_data(agent.name)
        except FileNotFoundError as e:
            return JSONResponse({'success': False, 'message': str(e)})
        except ValueError as e:
            return JSONResponse({'success': False, 'message': str(e)})

        agent_data['added_at'] = datetime.now().isoformat()
        
        with open(file_path, 'r') as f:
            index_data = json.load(f)

        if any(a['name'] == agent.name for a in index_data['agents']):
            return JSONResponse({'success': False, 'message': 'Agent already in index'})

        index_data['agents'].append(agent_data)

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/index/remove-plugin/{index_name}/{plugin_name}")
async def remove_plugin(index_name: str, plugin_name: str):
    """Remove a plugin from an index"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        index_data['plugins'] = [p for p in index_data['plugins'] if p['name'] != plugin_name]

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/index/remove-agent/{index_name}/{agent_name}")
async def remove_agent(index_name: str, agent_name: str):
    """Remove an agent from an index"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        index_data['agents'] = [a for a in index_data['agents'] if a['name'] != agent_name]

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/install/{index_name}")
async def install_index(index_name: str):
    """Install/track an index in the manifest"""
    try:
        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        manifest = load_plugin_manifest()
        if 'indices' not in manifest:
            manifest['indices'] = {'installed': {}}

        manifest['indices']['installed'][index_name] = {
            'url': index_data.get('url'),
            'last_sync': datetime.now().isoformat(),
            'trusted': index_data.get('trusted', False)
        }

        save_plugin_manifest(manifest)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
