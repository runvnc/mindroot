from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import json
import shutil

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

# In-memory storage for discovered plugins (replace with database in production)
plugins = {}

@router.post("/scan-directory")
async def scan_directory(request: DirectoryRequest):
    directory = request.directory
    if not os.path.isdir(directory):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    discovered_plugins = discover_plugins(directory)
    plugins.update(discovered_plugins)
    return {"message": f"Scanned {len(discovered_plugins)} plugins in {directory}"}

@router.get("/get-all-plugins")
async def get_all_plugins():
    return list(plugins.values())

@router.post("/install-local-plugin")
async def install_local_plugin(request: PluginRequest):
    plugin_name = request.plugin
    if plugin_name not in plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins[plugin_name]
    if plugin['state'] != 'available':
        raise HTTPException(status_code=400, detail="Plugin is not in an installable state")
    
    install_plugin(plugin)
    return {"message": f"Plugin {plugin_name} installed successfully"}

@router.post("/install-github-plugin")
async def install_github_plugin(request: GitHubPluginRequest):
    plugin_name = request.plugin
    github_url = request.url
    
    install_github_plugin(plugin_name, github_url)
    return {"message": f"Plugin {plugin_name} installed successfully from GitHub"}

@router.post("/update-plugin")
async def update_plugin(request: PluginRequest):
    plugin_name = request.plugin
    if plugin_name not in plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins[plugin_name]
    if plugin['state'] != 'installed':
        raise HTTPException(status_code=400, detail="Plugin is not installed")
    
    update_plugin(plugin)
    return {"message": f"Plugin {plugin_name} updated successfully"}

@router.post("/toggle-plugin")
async def toggle_plugin(request: TogglePluginRequest):
    plugin_name = request.plugin
    if plugin_name not in plugins:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    plugin = plugins[plugin_name]
    if plugin['state'] != 'installed':
        raise HTTPException(status_code=400, detail="Plugin is not installed")
    
    toggle_plugin_state(plugin, request.enabled)
    return {"message": f"Plugin {plugin_name} {'enabled' if request.enabled else 'disabled'} successfully"}

# Helper functions
def discover_plugins(directory):
    discovered = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path) and is_valid_plugin(item_path):
            plugin_info = load_plugin_info(item_path)
            plugin_info['source'] = directory
            plugin_info['state'] = 'available'
            discovered[plugin_info['name']] = plugin_info
    return discovered

def is_valid_plugin(path):
    return os.path.isfile(os.path.join(path, 'plugin_info.json')) and \
           os.path.isfile(os.path.join(path, '__init__.py'))

def load_plugin_info(path):
    with open(os.path.join(path, 'plugin_info.json'), 'r') as f:
        return json.load(f)

def install_plugin(plugin):
    # Implement plugin installation logic
    plugin['state'] = 'installed'

def install_github_plugin(plugin_name, github_url):
    # Implement GitHub clone and installation logic
    pass

def update_plugin(plugin):
    # Implement plugin update logic
    pass

def toggle_plugin_state(plugin, enabled):
    plugin['enabled'] = enabled
