from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import traceback
import os
import json
from lib.plugins import (
    load_plugin_manifest, update_plugin_manifest, plugin_install,
    save_plugin_manifest,
    plugin_update, toggle_plugin_state, get_plugin_path
)

router = APIRouter()

class DirectoryRequest(BaseModel):
    directory: str

class PluginRequest(BaseModel):
    plugin: str

class GitHubPluginRequest(BaseModel):
    plugin: str
    url: str

class TogglePluginRequest(BaseModel):
    plugin: str
    enabled: bool

@router.post("/scan-directory")
async def scan_directory(request: DirectoryRequest):
    print("request", request)
    print("dir", request.directory)
    directory = request.directory
    try:
        if not os.path.isdir(directory):
            return {"success": False, "message": "Invalid directory path"}
        
        print(f"Scanning directory {directory}")
        discovered_plugins = discover_plugins(directory)

        manifest = load_plugin_manifest()
        manifest['plugins']['available'].update(discovered_plugins)
        save_plugin_manifest(manifest)

        return {"success": True, "message": f"Scanned {len(discovered_plugins)} plugins in {directory}"}
    except PermissionError:
        return {"success": False, "message": f"Permission denied: Unable to access directory {directory}"}
    except json.JSONDecodeError:
        return {"success": False, "message": "Error reading plugin info: Invalid JSON format"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Unexpected error during directory scan: {str(e)}\n\n{trace}"}


@router.get("/get-all-plugins")
async def get_all_plugins():
    manifest = load_plugin_manifest()
    plugins = []
    for category, category_plugins in manifest['plugins'].items():
        for plugin_name, plugin_info in category_plugins.items():
            if plugin_info is None:
                continue
            if not 'enabled' in plugin_info:
                print(f"Plugin {plugin_name} has no enabled key")
                print("Skipping")
                continue
            plugins.append({
                "name": plugin_name,
                "category": category,
                "enabled": plugin_info['enabled'],
                "source": plugin_info['source'],
                "source_path": plugin_info.get('source_path'),
                "state": "installed" if category != 'available' else "available",
                "version": plugin_info.get('version', "0.0.1")
            })
    return {"success": True, "data": plugins}

@router.post("/install-local-plugin")
async def install_local_plugin(request: PluginRequest):
    plugin_name = request.plugin
    manifest = load_plugin_manifest()
    #if plugin_name not in manifest['plugins']['available']:
    #    return {"success": False, "message": "Plugin not found"}
    
    plugin_path = get_plugin_path(plugin_name)
    print(f"DEBUG: Attempting to install local plugin: {plugin_name} from path: {plugin_path}")
    if not plugin_path:
        return {"success": False, "message": "Plugin path not found"}
    
    try:
        plugin_install(plugin_name, source='available', source_path=plugin_path)
        return {"success": True, "message": f"Plugin {plugin_name} installed successfully"}
    except ValueError as e:
        return {"success": False, "message": f"Invalid input: {str(e)}"}
    except RuntimeError as e:
        return {"success": False, "message": str(e)}  # This will now include the pip error message
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}



@router.post("/install-x-github-plugin")
async def install_github_plugin(request: GitHubPluginRequest):
    github_url = request.url
    try:
        plugin_install('read_manifest', source='github', source_path=github_url)
        return {"success": True, "message": f"Plugin installed successfully from GitHub"}
    except ValueError as e:
        return {"success": False, "message": f"Invalid input: {str(e)}"}
    except RuntimeError as e:
        return {"success": False, "message": f"Installation failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


@router.post("/update-plugin")
async def update_plugin(request: PluginRequest):
    plugin_name = request.plugin
    if not get_plugin_path(plugin_name):
        return {"success": False, "message": "Plugin not found"}
    
    try:
        success = plugin_update(plugin_name)
        if success:
            return {"success": True, "message": f"Plugin {plugin_name} updated successfully"}
        else:
            return {"success": False, "message": "Failed to update plugin"}
    except ValueError as e:
        return {"success": False, "message": f"Invalid input: {str(e)}"}
    except RuntimeError as e:
        return {"success": False, "message": f"Update failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


@router.post("/toggle-plugin")
async def toggle_plugin(request: TogglePluginRequest):
    plugin_name = request.plugin
    if not get_plugin_path(plugin_name):
        return {"success": False, "message": "Plugin not found"}
    
    try:
        success = toggle_plugin_state(plugin_name, request.enabled)
        if success:
            return {"success": True, "message": f"Plugin {plugin_name} {'enabled' if request.enabled else 'disabled'} successfully"}
        else:
            return {"success": False, "message": "Failed to toggle plugin state"}
    except ValueError as e:
        return {"success": False, "message": f"Invalid input: {str(e)}"}
    except RuntimeError as e:
        return {"success": False, "message": f"Toggle operation failed: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}


# Helper function
def discover_plugins(directory):
    print("discover_plugins")
    print(f"Scanning directory: {directory}")
    discovered = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        print(f"Checking item: {item_path}")
        is_plugin_info = os.path.isfile(item_path) and item_path.endswith('plugin_info.json')
        if is_plugin_info:
            full_path = item_path
            source_path = directory
        else:
            full_path = os.path.join(item_path, 'plugin_info.json')
            source_path = item_path
        if is_plugin_info or os.path.isdir(item_path) and os.path.isfile(full_path):
            with open(full_path, 'r') as f:
                plugin_info = json.load(f)
            plugin_info['enabled'] = False
            plugin_info['source'] = 'available'
            plugin_info['source_path'] = source_path
            discovered[plugin_info['name']] = plugin_info

    return discovered
