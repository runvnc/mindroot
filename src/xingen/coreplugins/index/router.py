import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter()

# Define the directory where index files will be stored
# the instance path is based on the process startup path
#
def get_instance_path():
    return Path(__file__).resolve().parent.parent.parent

INDEX_DIR = Path(get_instance_path()) / 'indices'

# Ensure index directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

@router.get("/index/list-indices")
async def list_indices():
    """List all available indices"""
    try:
        indices = []
        for file in INDEX_DIR.glob('*.json'):
            with open(file, 'r') as f:
                index_data = json.load(f)
                indices.append(index_data)
        return JSONResponse({'success': True, 'data': indices})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/create-index")
async def create_index(request: Request):
    """Create a new index"""
    try:
        data = await request.json()
        name = data.get('name')
        if not name:
            return JSONResponse({'success': False, 'message': 'Name is required'})

        # Create index file
        file_path = INDEX_DIR / f"{name}.json"
        if file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index already exists'})

        index_data = {
            'name': name,
            'description': data.get('description', ''),
            'version': data.get('version', '1.0.0'),
            'plugins': [],
            'agents': []
        }

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/update-index")
async def update_index(request: Request):
    """Update index metadata"""
    try:
        data = await request.json()
        name = data.get('name')
        if not name:
            return JSONResponse({'success': False, 'message': 'Name is required'})

        file_path = INDEX_DIR / f"{name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        # Update fields
        for field in ['name', 'description', 'version']:
            if field in data:
                index_data[field] = data[field]

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/add-plugin")
async def add_plugin(request: Request):
    """Add a plugin to an index"""
    try:
        data = await request.json()
        index_name = data.get('index')
        plugin_name = data.get('plugin')

        if not index_name or not plugin_name:
            return JSONResponse({'success': False, 'message': 'Index and plugin names are required'})

        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        # Load plugin manifest
        manifest_path = Path(get_instance_path()) / 'plugin_manifest.json'
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Find plugin in manifest
        plugin_data = None
        for category in ['core', 'installed', 'available']:
            if plugin_name in manifest['plugins'].get(category, {}):
                plugin_data = manifest['plugins'][category][plugin_name]
                plugin_data['name'] = plugin_name
                break

        if not plugin_data:
            return JSONResponse({'success': False, 'message': 'Plugin not found in manifest'})

        # Add to index
        with open(file_path, 'r') as f:
            index_data = json.load(f)

        # Check if plugin already exists
        if any(p['name'] == plugin_name for p in index_data['plugins']):
            return JSONResponse({'success': False, 'message': 'Plugin already in index'})

        index_data['plugins'].append(plugin_data)

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/add-agent")
async def add_agent(request: Request):
    """Add an agent to an index"""
    try:
        data = await request.json()
        index_name = data.get('index')
        agent_name = data.get('agent')

        if not index_name or not agent_name:
            return JSONResponse({'success': False, 'message': 'Index and agent names are required'})

        file_path = INDEX_DIR / f"{index_name}.json"
        if not file_path.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        # TODO: Load agent details from appropriate source
        agent_data = {
            'name': agent_name,
            'version': '1.0.0',
            # Add other agent metadata as needed
        }

        with open(file_path, 'r') as f:
            index_data = json.load(f)

        # Check if agent already exists
        if any(a['name'] == agent_name for a in index_data['agents']):
            return JSONResponse({'success': False, 'message': 'Agent already in index'})

        index_data['agents'].append(agent_data)

        with open(file_path, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/remove-plugin")
async def remove_plugin(request: Request):
    """Remove a plugin from an index"""
    try:
        data = await request.json()
        index_name = data.get('index')
        plugin_name = data.get('plugin')

        if not index_name or not plugin_name:
            return JSONResponse({'success': False, 'message': 'Index and plugin names are required'})

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

@router.post("/index/remove-agent")
async def remove_agent(request: Request):
    """Remove an agent from an index"""
    try:
        data = await request.json()
        index_name = data.get('index')
        agent_name = data.get('agent')

        if not index_name or not agent_name:
            return JSONResponse({'success': False, 'message': 'Index and agent names are required'})

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
