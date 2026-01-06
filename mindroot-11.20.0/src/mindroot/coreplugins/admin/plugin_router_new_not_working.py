from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
import json
from typing import Optional, List
from lib import plugins
from . import plugin_manager
from lib.auth.cognito import get_current_user
from lib.config import get_settings

# Import MCP components
try:
    from mindroot.coreplugins.mcp.enhanced_mod import enhanced_mcp_manager
    from mindroot.coreplugins.mcp.mod import MCPServer
except ImportError:
    # Mock objects if MCP plugin is not fully installed, to prevent startup crash
    enhanced_mcp_manager = None
    MCPServer = None

router = APIRouter()

class PluginUpdateRequest(BaseModel):
    plugins: dict

@router.post("/update-plugins")
def update_plugins(request: PluginUpdateRequest):
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
    try:
        return plugins.load_plugin_manifest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class GithubPublishRequest(BaseModel):
    repo: str
    registry_url: str

@router.post("/plugins/publish_from_github")
async def publish_from_github(request: GithubPublishRequest, authorization: Optional[str] = Header(None), user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authorized for Mindroot Admin")

    registry_token = None
    if authorization and authorization.startswith("Bearer "):
        registry_token = authorization.split(" ")[1]

    if not registry_token:
        raise HTTPException(status_code=401, detail="Registry auth token not provided")

    try:
        result = await plugin_manager.publish_plugin_from_github(request.repo, registry_token, request.registry_url)
        return {"message": f"Plugin '{result.get('title')}' published successfully!", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

class GithubPublishRequest(BaseModel):
    repo: str

@router.post("/plugins/publish_from_github")
async def publish_from_github(request: GithubPublishRequest, user: dict = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authorized")
    try:
        result = await plugin_manager.publish_plugin_from_github(request.repo, user)
        return {"message": "Plugin published successfully", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- MCP Integration Routes ---

class McpServerRequest(BaseModel):
    server_name: str

@router.get("/mcp/list")
async def list_mcp_servers(user: dict = Depends(get_current_user)):
    if not enhanced_mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    servers = [s.dict() for s in enhanced_mcp_manager.servers.values()]
    return {"success": True, "data": servers}

@router.post("/mcp/add")
async def add_mcp_server(server_config: MCPServer, user: dict = Depends(get_current_user)):
    if not enhanced_mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    try:
        # The server_config is a full MCPServer object from the registry
        enhanced_mcp_manager.add_server(server_config.name, server_config)
        return {"success": True, "message": f"Server '{server_config.name}' added."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/remove")
async def remove_mcp_server(request: McpServerRequest, user: dict = Depends(get_current_user)):
    if not enhanced_mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    try:
        await enhanced_mcp_manager.remove_server(request.server_name)
        return {"success": True, "message": f"Server '{request.server_name}' removed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/connect")
async def connect_mcp_server(request: McpServerRequest, user: dict = Depends(get_current_user)):
    if not enhanced_mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    try:
        success = await enhanced_mcp_manager.connect_server(request.server_name)
        if success:
            return {"success": True, "message": f"Server '{request.server_name}' connected."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to connect to server '{request.server_name}'. Check logs.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/disconnect")
async def disconnect_mcp_server(request: McpServerRequest, user: dict = Depends(get_current_user)):
    if not enhanced_mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    try:
        success = await enhanced_mcp_manager.disconnect_server(request.server_name)
        if success:
            return {"success": True, "message": f"Server '{request.server_name}' disconnected."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to disconnect from server '{request.server_name}'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

