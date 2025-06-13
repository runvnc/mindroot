import json
import logging
from datetime import datetime
from pathlib import Path
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from ..models import PluginEntry, PluginManifest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def get_installed_plugin_metadata(plugin_name: str) -> dict:
    """Get metadata from main plugin manifest"""
    try:
        manifest_path = Path('data/plugin_manifest.json')
        logger.debug(f"Reading main plugin manifest from: {manifest_path}")
        
        if not manifest_path.exists():
            raise ValueError(f"Main plugin manifest not found at {manifest_path}")

        with open(manifest_path) as f:
            manifest_data = json.load(f)

        # Find the plugin in the installed plugins section
        installed_plugins = manifest_data.get('plugins', {}).get('installed', {})
        print("installed_plugins", installed_plugins)
        plugin_data = installed_plugins.get(plugin_name)

        if not plugin_data:
            raise ValueError(f"Plugin {plugin_name} not found in manifest")

        logger.debug(f"Found plugin data in manifest: {plugin_data}")

        return {
            'commands': plugin_data.get('commands', []),
            'services': plugin_data.get('services', []),
            'dependencies': plugin_data.get('dependencies', [])
        }

    except Exception as e:
        logger.error(f"Error reading plugin manifest: {str(e)}")
        raise

async def create_distributable_entry(plugin: PluginEntry) -> dict:
    """Transform plugin entry to distributable format"""
    try:
        # Get metadata from main manifest using display name
        metadata = await get_installed_plugin_metadata(plugin.name)

        # Get the remote_source from plugin data
        if not plugin.remote_source and plugin.source_path:
            # Extract from source_path if needed
            plugin_id = Path(plugin.source_path).parent.name
            remote_source = f"runvnc/{plugin_id}"
        else:
            remote_source = plugin.remote_source or ''

        return {
            'name': plugin.name,
            'version': plugin.version,
            'description': plugin.description,
            'source': 'github',
            'github_url': f"https://github.com/{remote_source}",
            'commands': metadata['commands'],
            'services': metadata['services'],
            'dependencies': metadata['dependencies'],
            'added_at': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating distributable entry: {str(e)}")
        raise

async def add_plugin(INDEX_DIR: Path, index_name: str, plugin: PluginEntry):
    """Add a plugin to an index"""
    try:
        logger.debug(f"Adding plugin: {plugin.name} to index: {index_name}")
        logger.debug(f"Plugin data: {plugin.dict()}")

        index_dir = INDEX_DIR / index_name
        index_file = index_dir / 'index.json'
        
        if not index_file.exists():
            return JSONResponse({'success': False, 'message': 'Index not found'})

        # Early validation - check for required GitHub info
        has_github_info = (
            plugin.remote_source or 
            plugin.github_url or 
            getattr(plugin, 'metadata', {}).get('github_url')
        )
        
        if not has_github_info:
            return JSONResponse({
                'success': False,
                'message': 'Plugin missing GitHub repository information. Cannot add to index.'
            })
        
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

        # Transform to distributable format
        try:
            plugin_data = await create_distributable_entry(plugin)
        except Exception as e:
            return JSONResponse({
                'success': False,
                'message': f'Failed to create distributable plugin entry: {str(e)}'
            })

        index_data['plugins'].append(plugin_data)

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

        # Remove from index data
        index_data['plugins'] = [p for p in index_data['plugins'] if p['name'] != plugin_name]

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        return JSONResponse({'success': True, 'data': index_data})
    except Exception as e:
        logger.error(f"Error removing plugin: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
