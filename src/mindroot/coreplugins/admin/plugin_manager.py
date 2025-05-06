from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
import os
import json
from typing import List, Optional
from lib.plugins import (
    load_plugin_manifest, update_plugin_manifest, plugin_install,
    save_plugin_manifest, plugin_update, toggle_plugin_state, get_plugin_path
)

router = APIRouter()

class DirectoryRequest(BaseModel):
    directory: str

class PluginRequest(BaseModel):
    plugin: str

class GitHubPluginRequest(BaseModel):
    plugin: str
    url: Optional[str] = None
    github_url: Optional[str] = None

class TogglePluginRequest(BaseModel):
    plugin: str
    enabled: bool

class InstallFromIndexRequest(BaseModel):
    plugin: str
    index_name: str

class PluginMetadata(BaseModel):
    description: Optional[str] = None
    commands: Optional[List[str]] = None
    services: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None

@router.get("/get-all-plugins")
async def get_all_plugins():
    try:
        manifest = load_plugin_manifest()
        plugins = []
        
        # Process core plugins
        for plugin_name, plugin_info in manifest['plugins']['core'].items():
            plugins.append({
                "name": plugin_name,
                "category": "core",
                "enabled": plugin_info['enabled'],
                "source": "core",
                "version": "1.0.0",
                "description": plugin_info.get('metadata', {}).get('description', '')
            })

        # Process installed plugins
        for plugin_name, plugin_info in manifest['plugins']['installed'].items():
            plugins.append({
                "name": plugin_name,
                "category": "installed",
                "enabled": plugin_info['enabled'],
                "source": plugin_info['source'],
                "source_path": plugin_info.get('source_path'),
                "version": plugin_info.get('version', '0.0.1'),
                "description": plugin_info.get('metadata', {}).get('description', ''),
                "index_source": plugin_info.get('metadata', {}).get('index_source')
            })

        return {"success": True, "data": plugins}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error fetching plugins: {str(e)}\n\n{trace}"}


@router.post("/scan-directory")
async def scan_directory(request: DirectoryRequest):
    try:
        directory = request.directory
        if not os.path.isdir(directory):
            return {"success": False, "message": "Invalid directory path"}
        
        discovered_plugins = discover_plugins(directory)
        manifest = load_plugin_manifest()
        print("discoverd_plugins", discovered_plugins)
        # Update installed plugins from discovered ones
        for plugin_name, plugin_info in discovered_plugins.items():
            plugin_info['source'] = 'local'
            plugin_info['metadata'] = {
                "description": plugin_info.get('description', ''),
                "install_date": plugin_info.get('install_date', ''),
                "commands": plugin_info.get('commands', []),
                "services": plugin_info.get('services', [])
            }
            print(plugin_info)
            manifest['plugins']['installed'][plugin_name] = plugin_info

        save_plugin_manifest(manifest)
        return {"success": True, "message": f"Scanned {len(discovered_plugins)} plugins in {directory}"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error during scan: {str(e)}\n\n{trace}"}

@router.post("/install-local-plugin")
async def install_local_plugin(request: PluginRequest):
    try:
        plugin_name = request.plugin
        plugin_path = get_plugin_path(plugin_name)
        
        if not plugin_path:
            return {"success": False, "message": "Plugin path not found"}
        
        success = await plugin_install(plugin_name, source='local', source_path=plugin_path)
        if success:
            return {"success": True, "message": f"Plugin {plugin_name} installed successfully"}
        else:
            return {"success": False, "message": "Installation failed"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing plugin: {str(e)}\n\n{trace}"}


@router.post("/install-x-github-plugin")
async def install_github_plugin(request: GitHubPluginRequest):
    try:
        print("Request:", request)
        url = request.url or request.github_url
        success = await plugin_install('test', source='github', source_path=url)
        if success:
            return {"success": True, "message": "Plugin installed successfully from GitHub"}
        else:
            return {"success": False, "message": "Installation failed"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing from GitHub: {str(e)}\n\n{trace}"}

@router.post("/install-from-index")
async def install_from_index(request: InstallFromIndexRequest):
    try:
        # Load the index to get plugin information
        index_path = os.path.join('indices', f"{request.index_name}.json")
        if not os.path.exists(index_path):
            return {"success": False, "message": "Index not found"}

        with open(index_path, 'r') as f:
            index_data = json.load(f)

        # Find plugin in index
        plugin_data = None
        for plugin in index_data.get('plugins', []):
            if plugin['name'] == request.plugin:
                plugin_data = plugin
                break

        if not plugin_data:
            return {"success": False, "message": "Plugin not found in index"}

        # Install the plugin
        if plugin_data.get('github_url'):
            success = await plugin_install(
                request.plugin,
                source='github',
                source_path=plugin_data['github_url']
            )
        elif plugin_data.get('source_path'):
            success = await plugin_install(
                request.plugin,
                source='local',
                source_path=plugin_data['source_path']
            )
        else:
            return {"success": False, "message": "No valid installation source in index"}

        if success:
            # Update plugin metadata with index information
            manifest = load_plugin_manifest()
            if request.plugin in manifest['plugins']['installed']:
                manifest['plugins']['installed'][request.plugin]['metadata']['index_source'] = request.index_name
                save_plugin_manifest(manifest)

            return {"success": True, "message": f"Plugin {request.plugin} installed successfully from index"}
        else:
            return {"success": False, "message": "Installation failed"}

    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing from index: {str(e)}\n\n{trace}"}


@router.post("/toggle-plugin")
async def toggle_plugin(request: TogglePluginRequest):
    try:
        success = toggle_plugin_state(request.plugin, request.enabled)
        if success:
            return {"success": True, "message": f"Plugin {request.plugin} {'enabled' if request.enabled else 'disabled'} successfully"}
        else:
            return {"success": False, "message": "Failed to toggle plugin state"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error toggling plugin: {str(e)}\n\n{trace}"}

# Helper function
def discover_plugins(directory):
    discovered = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        plugin_info_path = os.path.join(item_path, 'plugin_info.json')
        
        if os.path.isfile(plugin_info_path):
            try:
                with open(plugin_info_path, 'r') as f:
                    plugin_info = json.load(f)
                plugin_info['enabled'] = False
                plugin_info['source_path'] = item_path
                discovered[plugin_info['name']] = plugin_info
            except json.JSONDecodeError:
                print(f"Error reading plugin info for {item}")
                continue

    return discovered
