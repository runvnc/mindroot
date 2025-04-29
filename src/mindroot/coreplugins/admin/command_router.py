from fastapi import APIRouter, HTTPException
from lib.providers.services import service_manager
import os, json
from lib.plugins.installation import plugin_install
from lib.providers.missing import get_missing_commands
from lib.plugins.mapping import get_command_plugin_mapping
from lib.plugins.installation import install_recommended_plugins

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
        recommended_plugins = agent_data.get('recommended_plugins', agent_data.get('required_plugins', []))
        
        # Check which plugins are not installed
        pending_plugins = []
        for plugin_name in recommended_plugins:
            try:
                import pkg_resources
                pkg_resources.get_distribution(plugin_name)
            except pkg_resources.DistributionNotFound:
                pending_plugins.append(plugin_name)
                
        return {"pending_plugins": pending_plugins}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/install-recommended-plugins/{agent_name}")
async def install_agent_recommended_plugins(agent_name: str):
    """Install plugins recommended for an agent."""
    result = await install_recommended_plugins(agent_name)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
