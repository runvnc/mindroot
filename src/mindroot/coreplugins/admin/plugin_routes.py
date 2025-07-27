from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import json
import os
from typing import Optional
from lib import plugins
from . import plugin_manager
from lib.route_decorators import requires_role

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

class PluginUpdateRequest(BaseModel):
    plugins: dict

class GithubPublishRequest(BaseModel):
    repo: str
    registry_url: Optional[str] = None

# --- Plugin Management Routes ---

@router.post("/update-plugins")
def update_plugins(request: PluginUpdateRequest):
    """Update plugin enabled/disabled status."""
    try:
        with open('plugins.json', 'r') as file:
            plugins_data = json.load(file)

        for plugin in plugins_data:
            if plugin['name'] in request.plugins:
                plugin['enabled'] = request.plugins[plugin['name']]

        with open('plugins.json', 'w') as file:
            json.dump(plugins_data, file, indent=2)

        plugins.load('data/plugin_manifest.json')

        return {"message": "Plugins updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-plugins")
async def get_plugins():
    """Get list of all plugins."""
    try:
        return plugins.load_plugin_manifest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plugins/publish_from_github")
async def publish_plugin_from_github(
    request: GithubPublishRequest, 
    authorization: Optional[str] = Header(None)
):
    """Publish a plugin from GitHub repository to the registry.
    
    This endpoint allows publishing a plugin by simply providing the GitHub
    repository in the format 'username/repo'. It will fetch the plugin_info.json
    from the repository and publish it to the configured registry.
    
    The registry token can be provided via:
    1. Authorization header: "Bearer <token>"
    2. REGISTRY_TOKEN environment variable
    3. registry_token in data/registry_settings.json
    """
    try:
        # Get registry token from multiple sources
        registry_token = None
        
        # 1. Try Authorization header
        if authorization and authorization.startswith("Bearer "):
            registry_token = authorization.split(" ")[1]
        
        # 2. Try environment variable
        if not registry_token:
            registry_token = os.getenv('REGISTRY_TOKEN')
        
        # 3. Try settings file
        if not registry_token:
            try:
                settings_file = 'data/registry_settings.json'
                if os.path.exists(settings_file):
                    with open(settings_file, 'r') as f:
                        settings = json.load(f)
                        registry_token = settings.get('registry_token')
            except Exception as e:
                print(f"Error reading registry settings: {e}")
        
        if not registry_token:
            raise HTTPException(
                status_code=401, 
                detail="Registry authentication token not provided. Please provide via Authorization header, REGISTRY_TOKEN environment variable, or registry_settings.json file."
            )
        
        # Use the existing plugin_manager functionality
        registry_url = request.registry_url or "https://registry.mindroot.io"
        
        result = await plugin_manager.publish_plugin_from_github(
            request.repo, 
            registry_token, 
            registry_url
        )
        
        return {
            "success": True,
            "message": f"Plugin '{result.get('title', request.repo)}' published successfully!", 
            "data": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
