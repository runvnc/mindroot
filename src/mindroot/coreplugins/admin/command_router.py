from fastapi import APIRouter, HTTPException
from lib.providers.services import service_manager
from lib.plugins.installation import plugin_install
from lib.providers.missing import get_missing_commands
from lib.plugins.mapping import get_command_plugin_mapping

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
