from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import traceback
import os
import json
from typing import List, Optional
from lib.plugins import (
    load_plugin_manifest, update_plugin_manifest, plugin_install,
    save_plugin_manifest, plugin_update, toggle_plugin_state, get_plugin_path
)
from lib.plugins.installation import download_github_files
from lib.streamcmd import stream_command_as_events
import asyncio


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

class StreamInstallRequest(BaseModel):
    plugin: str
    source: str
    source_path: str = None

class PluginMetadata(BaseModel):
    description: Optional[str] = None
    commands: Optional[List[str]] = None
    services: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None

import sys, os, shlex

@router.post("/stream-install-plugin", response_class=EventSourceResponse)
async def stream_install_plugin(request: StreamInstallRequest):
    """Stream the installation process of a plugin using SSE (POST method)."""
    # Prepare the command based on the source
    if request.source == 'github_direct':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', request.source_path, '-v', '--no-cache-dir']
    elif request.source == 'local':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', request.source_path, '-v', '--no-cache-dir']
    elif request.source == 'pypi':
        cmd = [sys.executable, '-m', 'pip', 'install', request.plugin, '-v', '--no-cache-dir']
    else:
        return {"success": False, "message": "Invalid source"}

    # For GitHub installations, use the plugin_install function which handles the download and extraction
    if request.source == 'github':
        try:
            # Use the streaming approach for GitHub installations
            parts = request.source_path.split(':')
            repo_path = parts[0]
            tag = parts[1] if len(parts) > 1 else None
            
            async def stream_github_install():
                yield {"event": "message", "data": f"Downloading GitHub repository {repo_path}..."}
                
                try:
                    plugin_dir, _, plugin_info = download_github_files(repo_path, tag)
                    
                    cmd = [sys.executable, '-m', 'pip', 'install', '-e', plugin_dir, '-v', '--no-cache-dir']
                    async for event in stream_command_as_events(cmd):
                        yield event
                        
                    update_plugin_manifest(
                        plugin_info['name'], 'github', os.path.abspath(plugin_dir),
                        remote_source=repo_path, version=plugin_info.get('version', '0.0.1'),
                        metadata=plugin_info
                    )
                except Exception as e:
                    yield {"event": "error", "data": f"Error installing from GitHub: {str(e)}"}
            
            return EventSourceResponse(stream_github_install())
        except Exception as e:
            return {"success": False, "message": f"Error setting up GitHub installation: {str(e)}"}
    
    # For other sources, use our streamcmd module to stream the command output
    return EventSourceResponse(stream_command_as_events(cmd))
@router.get("/stream-install-plugin", response_class=EventSourceResponse)
async def stream_install_plugin_get(request: Request):
    """Stream the installation process of a plugin using SSE (GET method)."""
    # Extract parameters from query string
    plugin = request.query_params.get("plugin", "")
    source = request.query_params.get("source", "")
    source_path = request.query_params.get("source_path", "")
    
    # Use the new simpler approach
    if source == 'github':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', source_path, '-v', '--no-cache-dir']
        message = f"Installing {plugin} from GitHub repository {source_path}..."
    elif source == 'local':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', source_path, '-v', '--no-cache-dir']
        message = f"Installing from local path: {source_path}"
    elif source == 'pypi':
        cmd = [sys.executable, '-m', 'pip', 'install', plugin, '-v', '--no-cache-dir']
        message = f"Installing from PyPI: {plugin}"
    else:  
        return {"success": False, "message": "Invalid source"}

    # For GitHub installations, use the plugin_install function which handles the download and extraction
    if source == 'github':
        try:
            # Use the streaming approach for GitHub installations
            parts = source_path.split(':')
            repo_path = parts[0]
            tag = parts[1] if len(parts) > 1 else None
            
            # First yield a message about downloading
            async def stream_github_install():
                yield {"event": "message", "data": f"Downloading GitHub repository {repo_path}..."}
                
                # Download and extract the GitHub repository
                try:
                    plugin_dir, _, plugin_info = download_github_files(repo_path, tag)
                    
                    # Now stream the installation from the local directory
                    cmd = [sys.executable, '-m', 'pip', 'install', '-e', plugin_dir, '-v', '--no-cache-dir']
                    async for event in stream_command_as_events(cmd):
                        yield event
                        
                    # Update the plugin manifest
                    update_plugin_manifest(
                        plugin_info['name'], 'github', os.path.abspath(plugin_dir),
                        remote_source=repo_path, version=plugin_info.get('version', '0.0.1'),
                        metadata=plugin_info
                    )
                except Exception as e:
                    yield {"event": "error", "data": f"Error installing from GitHub: {str(e)}"}
            
            return EventSourceResponse(stream_github_install())
        except Exception as e:
            return {"success": False, "message": f"Error installing from GitHub: {str(e)}"}
    
    # Use our new streamcmd module
    return EventSourceResponse(stream_command_as_events(cmd))

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
                "remote_source": plugin_name,
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
                "remote_source": plugin_info.get('remote_source', plugin_info.get('github_url')),
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
        
        # Analyze plugins for index compatibility
        addable_count = 0
        for plugin_name, plugin_info in discovered_plugins.items():
            # Check if plugin has GitHub info
            has_github = (
                plugin_info.get('github_url') or 
                plugin_info.get('remote_source') or
                (plugin_info.get('metadata', {}).get('github_url'))
            )
            if has_github:
                addable_count += 1
        
        # Update installed plugins from discovered ones
        for plugin_name, plugin_info in discovered_plugins.items():
            plugin_info['source'] = 'local'
            plugin_info['metadata'] = plugin_info.get('metadata', {}) or {
                "description": plugin_info.get('description', ''),
                "install_date": plugin_info.get('install_date', ''),
                "commands": plugin_info.get('commands', []),
                "services": plugin_info.get('services', [])
            }
            print(plugin_info)
            manifest['plugins']['installed'][plugin_name] = plugin_info

        # Prepare plugin list for response
        plugins_list = [{
            "name": name,
            "description": info.get('metadata', {}).get('description', info.get('description', ''))
        } for name, info in discovered_plugins.items()]
        
        save_plugin_manifest(manifest)
        
        response = {"success": True, 
                   "message": f"Scanned {len(discovered_plugins)} plugins in {directory}",
                   "plugins": plugins_list,
                   "addable_to_index": addable_count}
        if addable_count < len(discovered_plugins):
            response["warning"] = f"{len(discovered_plugins) - addable_count} plugins missing GitHub info and cannot be added to indices"
        return response
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
