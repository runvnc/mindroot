import json
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from ..models import PluginEntry

async def add_plugin(INDEX_DIR: Path, index_name: str, plugin: PluginEntry):
    """Add a plugin to an index"""
    try:
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        # Check if plugin is local
        if plugin.source == 'local':
            return JSONResponse({
                'success': False, 
                'message': 'Local plugins cannot be added to an index'
            })

        with open(index_file, 'r') as f:
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

        # Save plugin metadata in plugins directory
        plugin_dir = index_dir / 'plugins' / plugin.name
        plugin_dir.mkdir(exist_ok=True)
        
        with open(plugin_dir / 'plugin.json', 'w') as f:
            json.dump(plugin_data, f, indent=2)

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def remove_plugin(INDEX_DIR: Path, index_name: str, plugin_name: str):
    """Remove a plugin from an index"""
    try:
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        with open(index_file, 'r') as f:
            index_data = json.load(f)

        index_data['plugins'] = [p for p in index_data['plugins'] if p['name'] != plugin_name]

        # Remove plugin directory
        plugin_dir = index_dir / 'plugins' / plugin_name
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
