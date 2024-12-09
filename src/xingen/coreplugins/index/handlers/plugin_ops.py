import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from ..models import PluginEntry

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_safe_plugin_name(plugin: PluginEntry) -> str:
    """Extract a filesystem-safe name from plugin metadata"""
    if plugin.source == 'github' and plugin.remote_source:
        # For GitHub plugins, use the repo name from remote_source
        safe_name = plugin.remote_source.split('/')[-1]
        logger.debug(f"Using remote_source for safe name: {safe_name}")
        return safe_name
    elif plugin.source_path:
        # Get the last component of the path
        safe_name = Path(plugin.source_path).name
        logger.debug(f"Using source_path for safe name: {safe_name}")
        return safe_name
    else:
        # Fallback to a sanitized version of the display name
        safe_name = plugin.name.replace(' ', '_').replace('(', '').replace(')', '').lower()
        logger.debug(f"Using sanitized display name for safe name: {safe_name}")
        return safe_name

def ensure_directory_structure(index_dir: Path):
    """Ensure all required directories exist"""
    plugins_dir = index_dir / 'plugins'
    logger.debug(f"Ensuring plugins directory exists: {plugins_dir}")
    plugins_dir.mkdir(parents=True, exist_ok=True)
    return plugins_dir

async def add_plugin(INDEX_DIR: Path, index_name: str, plugin: PluginEntry):
    """Add a plugin to an index"""
    try:
        logger.debug(f"Adding plugin: {plugin.name} to index: {index_name}")
        logger.debug(f"Plugin data: {plugin.dict()}")
        
        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        logger.debug(f"Index directory: {index_dir}")
        logger.debug(f"Index file: {index_file}")
        
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
            'remote_source': plugin.remote_source,
            'commands': plugin.commands,
            'services': plugin.services,
            'dependencies': plugin.dependencies,
            'added_at': datetime.now().isoformat()
        }

        index_data['plugins'].append(plugin_data)

        # Ensure directory structure exists and get safe name
        plugins_dir = ensure_directory_structure(index_dir)
        safe_name = get_safe_plugin_name(plugin)
        
        logger.debug(f"Using safe name for plugin directory: {safe_name}")
        logger.debug(f"Full plugin directory path will be: {plugins_dir / safe_name}")
        
        # Create plugin directory
        plugin_dir = plugins_dir / safe_name
        logger.debug(f"Creating plugin directory: {plugin_dir}")
        plugin_dir.mkdir(exist_ok=True)
        
        logger.debug(f"Writing plugin.json to: {plugin_dir / 'plugin.json'}")
        with open(plugin_dir / 'plugin.json', 'w') as f:
            json.dump(plugin_data, f, indent=2)

        logger.debug(f"Updating index.json")
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        logger.error(f"Error adding plugin: {str(e)}", exc_info=True)
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

        # Find the plugin data first to get source info
        plugin_data = next((p for p in index_data['plugins'] if p['name'] == plugin_name), None)
        if plugin_data:
            # Create temporary PluginEntry to get safe name
            temp_plugin = PluginEntry(
                name=plugin_data['name'],
                source=plugin_data.get('source', ''),
                source_path=plugin_data.get('source_path', ''),
                remote_source=plugin_data.get('remote_source', ''),
                version=plugin_data.get('version', '1.0.0')
            )
            safe_name = get_safe_plugin_name(temp_plugin)
            
            # Ensure plugins directory exists
            plugins_dir = ensure_directory_structure(index_dir)
            
            # Remove plugin directory using safe name
            plugin_dir = plugins_dir / safe_name
            if plugin_dir.exists():
                shutil.rmtree(plugin_dir)

        # Remove from index data
        index_data['plugins'] = [p for p in index_data['plugins'] if p['name'] != plugin_name]

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        logger.error(f"Error removing plugin: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
