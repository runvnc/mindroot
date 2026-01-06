from fastapi import APIRouter, HTTPException
from lib.providers.services import service_manager
import os, json
from lib.plugins.installation import plugin_install
from lib.providers.missing import get_missing_commands
from lib.plugins.mapping import get_command_plugin_mapping
from pathlib import Path
from lib.plugins.installation import install_recommended_plugins, download_github_files
from lib.plugins.manifest import update_plugin_manifest
# For Server-Sent Events (streamed logs)
from sse_starlette.sse import EventSourceResponse
from lib.streamcmd import stream_command_as_events
import contextlib, io, json, asyncio, sys

router = APIRouter()

# Global installation queue
plugin_install_queue = []

@router.get("/admin/missing-commands/{agent_name}")
async def missing_commands(agent_name: str):
    """Get commands mentioned in agent instructions but not available."""
    result = await get_missing_commands(agent_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# ------------------------------------------------------------------
#  NEW:  Stream installation of recommended plugins with live logs
# ------------------------------------------------------------------

@router.get("/admin/stream-install-recommended-plugins/{agent_name}", response_class=EventSourceResponse)
async def stream_install_recommended_plugins(agent_name: str):
    """
    SSE endpoint that installs all recommended plugins for `agent_name`
    and streams stdout/stderr lines back to the browser.  It finishes by
    sending a JSON summary and the literal string 'END'.
    """

    async def event_generator():
        try:
            # Load agent data
            agent_path = f"data/agents/local/{agent_name}/agent.json"
            if not os.path.exists(agent_path):
                agent_path = f"data/agents/shared/{agent_name}/agent.json"
                
            if not os.path.exists(agent_path):
                yield f"Error: Agent {agent_name} not found\n"
                yield "END\n"
                return
                
            with open(agent_path, 'r') as f:
                agent_data = json.load(f)
                
            # Get recommended plugins
            recommended_plugins = agent_data.get('recommended_plugins', agent_data.get('required_plugins', []))
            
            if not recommended_plugins:
                yield "No recommended plugins found for this agent\n"
                yield "END\n"
                return
            
            yield f"Installing {len(recommended_plugins)} recommended plugins for {agent_name}...\n"
            
            results = []
            
            # Install each plugin and stream the output
            for plugin_source in recommended_plugins:
                plugin_name = plugin_source.split('/')[-1]
                
                yield f"\n=== Installing {plugin_name} ===\n"
                
                try:
                    # Check if already installed
                    import pkg_resources
                    try:
                        pkg_resources.get_distribution(plugin_name)
                        yield f"{plugin_name} is already installed\n"
                        results.append({"plugin": plugin_name, "status": "already_installed"})
                        continue
                    except pkg_resources.DistributionNotFound:
                        pass
                    
                    # Determine installation source
                    if '/' in plugin_source:  # GitHub format
                        yield f"Installing from GitHub: {plugin_source}\n"
                        
                        # Download and extract
                        plugin_dir, _, plugin_info = download_github_files(plugin_source)
                        
                        # Stream the pip install
                        cmd = [sys.executable, '-m', 'pip', 'install', '-e', plugin_dir, '-v']
                        async for event in stream_command_as_events(cmd):
                            if event.get('event') == 'message':
                                yield event['data'] + "\n"
                            elif event.get('event') == 'warning':
                                yield "WARNING: " + event['data'] + "\n"
                            elif event.get('event') == 'error':
                                yield "ERROR: " + event['data'] + "\n"
                            elif event.get('event') == 'complete':
                                # Update the plugin manifest after successful installation
                                update_plugin_manifest(
                                    plugin_info['name'],
                                    'github',
                                    os.path.abspath(plugin_dir),
                                    remote_source=plugin_source,
                                    version=plugin_info.get('version', '0.0.1'),
                                    metadata=plugin_info
                                )
                        
                        results.append({"plugin": plugin_name, "status": "success", "source": "github", "source_path": plugin_source})
                    else:
                        # PyPI installation
                        yield f"Installing from PyPI: {plugin_name}\n"
                        cmd = [sys.executable, '-m', 'pip', 'install', plugin_name, '-v']
                        async for event in stream_command_as_events(cmd):
                            if event.get('event') == 'message':
                                yield event['data'] + "\n"
                            elif event.get('event') == 'warning':
                                yield "WARNING: " + event['data'] + "\n"
                            elif event.get('event') == 'error':
                                yield "ERROR: " + event['data'] + "\n"
                            elif event.get('event') == 'complete':
                                # Update the plugin manifest for PyPI install
                                update_plugin_manifest(plugin_name, 'pypi', None)
                        
                        results.append({"plugin": plugin_name, "status": "success", "source": "pypi"})
                        
                except Exception as e:
                    yield f"ERROR: Failed to install {plugin_name}: {str(e)}\n"
                    results.append({"plugin": plugin_name, "status": "error", "message": str(e)})
            
            # Send results and END
            yield "\n" + json.dumps({"results": results}) + "\n"
            yield "END"
            
        except Exception as e:
            yield f"ERROR: {str(e)}\n"
            yield "END"

    return EventSourceResponse(event_generator())

@router.get("/admin/command-plugin-mapping")
async def command_plugin_mapping():
    """Get mapping of commands to plugins that provide them."""
    return await get_command_plugin_mapping()

@router.post("/admin/queue-plugin-install")
async def queue_plugin_install(plugin_name: str, source: str, source_path: str, remote_source: str = None):
    """Queue a plugin for installation."""
    # Check if plugin is already in queue
    for item in plugin_install_queue:
        if item['plugin_name'] == plugin_name:
            return {"status": "already_queued", "plugin": plugin_name}
    
    # Add to installation queue
    plugin_install_queue.append({
        'plugin_name': plugin_name,
        'source': source,
        'source_path': source_path,
        'remote_source': remote_source
    })
    
    return {"status": "queued", "plugin": plugin_name}

@router.post("/admin/install-queued-plugins")
async def install_queued_plugins():
    """Install all queued plugins."""
    results = []
    
    for item in plugin_install_queue.copy():
        try:
            await plugin_install(
                item['plugin_name'],
                item['source'],
                item['source_path'],
                item['remote_source']
            )
            results.append({
                'plugin_name': item['plugin_name'],
                'status': 'success'
            })
            plugin_install_queue.remove(item)
        except Exception as e:
            results.append({
                'plugin_name': item['plugin_name'],
                'status': 'error',
                'message': str(e)
            })
    
    return {"status": "completed", "results": results}

@router.get("/admin/check-recommended-plugins/{agent_name}")
async def check_recommended_plugins(agent_name: str):
    """Check which recommended plugins are not installed."""
    try:
        # Load agent data
        agent_path = f"data/agents/local/{agent_name}/agent.json"
        if not os.path.exists(agent_path):
            agent_path = f"data/agents/shared/{agent_name}/agent.json"
            
        if not os.path.exists(agent_path):
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
            
        with open(agent_path, 'r') as f:
            agent_data = json.load(f)
            
        # Get recommended plugins
        recommended_plugins = agent_data.get('recommended_plugins')
        
        pending_plugins = []
        plugin_sources = {}
        
        # Define indices directory path
        indices_dir = Path("indices")
        data_indices_dir = Path("data/indices")
        
        # Determine which indices directory exists
        if data_indices_dir.exists():
            indices_dir = data_indices_dir
        
        # Get all available indices
        available_indices = []
        for index_file in indices_dir.glob("*.json"):
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
                    available_indices.append(index_data)
            except Exception as e:
                print(f"Error reading index file {index_file}: {str(e)}")
        
        # Check each recommended plugin
        for plugin_source in recommended_plugins:
            try:
                # if there is a slash, the name is the last part
                plugin_name = plugin_source.split('/')[-1]
                # First check if plugin is already installed
                try:
                    import pkg_resources
                    pkg_resources.get_distribution(plugin_name)
                    continue  # Plugin is installed, skip to next
                except pkg_resources.DistributionNotFound:
                    # Plugin is not installed, look for it in indices
                    found = False
                    for index in available_indices:
                        for plugin in index.get('plugins', []):
                            if plugin.get('name') == plugin_name:
                                # Found the plugin in an index
                                remote_source = plugin.get('remote_source')
                                github_url = plugin.get('github_url')
                                
                                # Extract GitHub repo path if available
                                if github_url and 'github.com/' in github_url:
                                    github_path = github_url.split('github.com/')[1]
                                    plugin_sources[plugin_name] = github_path
                                elif remote_source:
                                    plugin_sources[plugin_name] = remote_source
                                
                                found = True
                                break
                    
                    if not found:
                        # If not found in indices, use the name as is
                        plugin_sources[plugin_name] = plugin_name
                    
                    pending_plugins.append(plugin_name)
            except Exception as e:
                print(f"Error checking plugin {plugin_name}: {str(e)}")
                pending_plugins.append(plugin_name)
        
        return {"pending_plugins": pending_plugins, "plugin_sources": plugin_sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
@router.post("/admin/install-recommended-plugins/{agent_name}")
async def install_agent_recommended_plugins(agent_name: str):
    """Install plugins recommended for an agent."""
    result = await install_recommended_plugins(agent_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# ------------------------------------------------------------------
#  NEW:  Stream installation of recommended plugins with live logs
# ------------------------------------------------------------------

@router.get("/admin/stream-install-recommended-plugins/{agent_name}", response_class=EventSourceResponse)
async def stream_install_recommended_plugins(agent_name: str):
    """
    SSE endpoint that installs all recommended plugins for `agent_name`
    and streams stdout/stderr lines back to the browser.  It finishes by
    sending a JSON summary and the literal string 'END'.
    """

    async def event_generator():
        try:
            # Load agent data
            agent_path = f"data/agents/local/{agent_name}/agent.json"
            if not os.path.exists(agent_path):
                agent_path = f"data/agents/shared/{agent_name}/agent.json"
                
            if not os.path.exists(agent_path):
                yield f"Error: Agent {agent_name} not found\n"
                yield "END\n"
                return
                
            with open(agent_path, 'r') as f:
                agent_data = json.load(f)
                
            # Get recommended plugins
            recommended_plugins = agent_data.get('recommended_plugins', agent_data.get('required_plugins', []))
            
            if not recommended_plugins:
                yield "No recommended plugins found for this agent\n"
                yield "END\n"
                return
            
            yield f"Installing {len(recommended_plugins)} recommended plugins for {agent_name}...\n"
            
            results = []
            
            # Install each plugin and stream the output
            for plugin_source in recommended_plugins:
                plugin_name = plugin_source.split('/')[-1]
                
                yield f"\n=== Installing {plugin_name} ===\n"
                
                try:
                    # Check if already installed
                    import pkg_resources
                    try:
                        pkg_resources.get_distribution(plugin_name)
                        yield f"{plugin_name} is already installed\n"
                        results.append({"plugin": plugin_name, "status": "already_installed"})
                        continue
                    except pkg_resources.DistributionNotFound:
                        pass
                    
                    # Determine installation source
                    if '/' in plugin_source:  # GitHub format
                        yield f"Installing from GitHub: {plugin_source}\n"
                        
                        # Download and extract
                        plugin_dir, _, plugin_info = download_github_files(plugin_source)
                        
                        # Stream the pip install
                        cmd = [sys.executable, '-m', 'pip', 'install', '-e', plugin_dir, '-v']
                        async for event in stream_command_as_events(cmd):
                            if event.get('event') == 'message':
                                yield event['data'] + "\n"
                            elif event.get('event') == 'warning':
                                yield "WARNING: " + event['data'] + "\n"
                            elif event.get('event') == 'error':
                                yield "ERROR: " + event['data'] + "\n"
                            elif event.get('event') == 'complete':
                                # Update the plugin manifest after successful installation
                                update_plugin_manifest(
                                    plugin_info['name'],
                                    'github',
                                    os.path.abspath(plugin_dir),
                                    remote_source=plugin_source,
                                    version=plugin_info.get('version', '0.0.1'),
                                    metadata=plugin_info
                                )
                        
                        results.append({"plugin": plugin_name, "status": "success", "source": "github", "source_path": plugin_source})
                    else:
                        # PyPI installation
                        yield f"Installing from PyPI: {plugin_name}\n"
                        cmd = [sys.executable, '-m', 'pip', 'install', plugin_name, '-v']
                        async for event in stream_command_as_events(cmd):
                            if event.get('event') == 'message':
                                yield event['data'] + "\n"
                            elif event.get('event') == 'warning':
                                yield "WARNING: " + event['data'] + "\n"
                            elif event.get('event') == 'error':
                                yield "ERROR: " + event['data'] + "\n"
                            elif event.get('event') == 'complete':
                                # Update the plugin manifest for PyPI install
                                update_plugin_manifest(plugin_name, 'pypi', None)
                        
                        results.append({"plugin": plugin_name, "status": "success", "source": "pypi"})
                        
                except Exception as e:
                    yield f"ERROR: Failed to install {plugin_name}: {str(e)}\n"
                    results.append({"plugin": plugin_name, "status": "error", "message": str(e)})
            
            # Send results and END
            yield "\n" + json.dumps({"results": results}) + "\n"
            yield "END"
            
        except Exception as e:
            yield f"ERROR: {str(e)}\n"
            yield "END"

    return EventSourceResponse(event_generator())
