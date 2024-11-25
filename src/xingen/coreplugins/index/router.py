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

@router.get("/index/list-indices")
async def list_indices():
    """List all available indices"""
    try:
        indices = []
        #if there are no indices, copy the default.json file from the SCRIPT dir to the indices folder
        if not any(INDEX_DIR.glob('*.json')):
            this_script_path = Path(__file__).parent
            default_index_path = this_script_path / 'default.json'
        with open(default_index_path, 'r') as f:
            default_index_data = json.load(f)
            with open(INDEX_DIR / 'default.json', 'w') as f:
                json.dump(default_index_data, f, indent=2)

        for file in INDEX_DIR.glob('*.json'):
            with open(file, 'r') as f:
                index_data = json.load(f)
                # Add installed status from manifest
                manifest = load_plugin_manifest()
                index_data['installed'] = file.stem in manifest.get('indices', {}).get('installed', {})
                indices.append(index_data)
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

        # Update metadata fields
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

        # Check if plugin already exists
        if any(p['name'] == plugin.name for p in index_data['plugins']):
            return JSONResponse({'success': False, 'message': 'Plugin already in index'})

        # Add plugin with full metadata
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

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        # Check if agent already exists
        if any(a['name'] == agent.name for a in index_data['agents']):
            return JSONResponse({'success': False, 'message': 'Agent already in index'})

        # Add agent with full metadata
        agent_data = {
            'name': agent.name,
            'version': agent.version,
            'description': agent.description,
            'required_commands': agent.required_commands,
            'required_services': agent.required_services,
            'added_at': datetime.now().isoformat()
        }

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

        # Update manifest to track installed index
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
