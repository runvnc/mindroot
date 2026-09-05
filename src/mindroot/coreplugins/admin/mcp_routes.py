from fastapi import APIRouter, HTTPException
import os
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from lib.route_decorators import requires_role
try:
    from mindroot.coreplugins.mcp_.mod import mcp_manager, MCPServer
except ImportError:
    try:
        from mindroot.coreplugins.mcp.mod import mcp_manager, MCPServer
    except ImportError:
        mcp_manager = None
        MCPServer = None
router = APIRouter(dependencies=[requires_role('admin')])

class McpLocalTestRequest(BaseModel):
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    secrets: Optional[Dict[str, str]] = None

class McpServerRequest(BaseModel):
    server_name: str

class McpConnectRequest(BaseModel):
    server_name: str
    secrets: Optional[Dict[str, str]] = None

class McpServerAddRequest(BaseModel):
    name: str
    description: str
    command: Optional[str] = None
    args: List[str] = []
    env: dict = {}
    transport: str = 'stdio'
    url: Optional[str] = None
    provider_url: Optional[str] = None
    transport_url: Optional[str] = None
    transport_type: Optional[str] = None
    auth_type: str = 'none'
    auth_headers: Dict[str, str] = {}
    authorization_server_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: List[str] = []
    redirect_uri: Optional[str] = None

class McpOAuthCallbackRequest(BaseModel):
    server_name: str
    code: str
    state: Optional[str] = None

@router.get('/mcp/list')
async def list_mcp_servers():
    """List all configured MCP servers."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    try:
        servers = []
        for name, server in mcp_manager.servers.items():
            servers.append({'name': name, 'description': server.description, 'status': server.status, 'transport': server.transport, 'command': server.command, 'args': server.args, 'capabilities': server.capabilities})
        return {'success': True, 'data': servers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/mcp/add')
async def add_mcp_server(server_request: McpServerAddRequest):
    """Add a new MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    try:
        if server_request.transport == 'stdio' and (not server_request.command):
            raise HTTPException(status_code=400, detail='Command is required for stdio transport')
        if server_request.transport in ['http', 'sse', 'websocket'] and (not server_request.url):
            raise HTTPException(status_code=400, detail='URL is required for remote transports')
        server = MCPServer(name=server_request.name, description=server_request.description, command=server_request.command or '', args=server_request.args, env=server_request.env, transport=server_request.transport, url=server_request.url, auth_type=server_request.auth_type, auth_headers=server_request.auth_headers, authorization_server_url=server_request.authorization_server_url, client_id=server_request.client_id, client_secret=server_request.client_secret, scopes=server_request.scopes, redirect_uri=server_request.redirect_uri or f'{server_request.url}/oauth/callback' if server_request.url else None)
        if not server.redirect_uri and server_request.auth_type == 'oauth2':
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            server.redirect_uri = f'{base_url}/mcp_oauth_cb'
        mcp_manager.add_server(server_request.name, server)
        return {'success': True, 'message': f"MCP server '{server_request.name}' added successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/mcp/remove')
async def remove_mcp_server(request: McpServerRequest):
    """Remove an MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    try:
        if request.server_name in mcp_manager.sessions:
            await mcp_manager.disconnect_server(request.server_name)
        mcp_manager.remove_server(request.server_name)
        return {'success': True, 'message': f"MCP server '{request.server_name}' removed successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/mcp/connect')
async def connect_mcp_server(request: McpConnectRequest):
    """Connect to an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    if request.secrets:
        if request.server_name in mcp_manager.servers:
            server = mcp_manager.servers[request.server_name]
            if server.secrets is None:
                server.secrets = {}
            server.secrets.update(request.secrets)
            mcp_manager.save_config()
    try:
        success = await mcp_manager.connect_server(request.server_name, secrets=request.secrets)
        if success:
            return {'success': True, 'message': f"MCP server '{request.server_name}' connected successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to connect to MCP server '{request.server_name}'. Check logs for details.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/mcp/disconnect')
async def disconnect_mcp_server(request: McpServerRequest):
    """Disconnect from an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    try:
        success = await mcp_manager.disconnect_server(request.server_name)
        if success:
            return {'success': True, 'message': f"MCP server '{request.server_name}' disconnected successfully."}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to disconnect from MCP server '{request.server_name}'.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Debug logging for MCP install route
_MCP_INSTALL_DEBUG = True
import traceback as _mcp_tb

class McpRegistryInstallRequest(BaseModel):
    """Request model for MCP server install from registry"""
    registry_id: Union[int, str]
    registry_url: Optional[str] = None
    secrets: Optional[Dict[str, str]] = None

@router.post('/mcp/install')
async def mcp_install_registry(request: McpRegistryInstallRequest):
    """Install an MCP server from the registry (frontend-facing endpoint).
    
    This is the route called by the frontend JS (registry-shared-services.js).
    It delegates to the registry install logic.
    """
    # Normalize registry_id to string (frontend sends int)
    registry_id_str = str(request.registry_id)
    
    print(f"[MCP_INSTALL_DEBUG] POST /admin/mcp/install called with registry_id={request.registry_id}, registry_url={request.registry_url}, secrets_keys={list(request.secrets.keys()) if request.secrets else None}")
    
    if not mcp_manager:
        print("[MCP_INSTALL_DEBUG] mcp_manager is None - MCP plugin not loaded")
        raise HTTPException(status_code=501, detail='MCP Plugin not available')
    
    try:
        # Import and call the registry install logic
        from .mcp_registry_routes import install_registry_server, RegistryServerInstallRequest
        
        # The mcp_registry_routes.install_registry_server expects a
        # RegistryServerInstallRequest with registry_id and optional server_name.
        # Our frontend sends registry_id, registry_url, and optional secrets.
        # Build a compatible request.
        inner_request = RegistryServerInstallRequest(
            registry_id=registry_id_str,
            server_name=None
        )
        
        print(f"[MCP_INSTALL_DEBUG] Delegating to install_registry_server with registry_id={registry_id_str}")
        
        result = await install_registry_server(inner_request)
        
        # If secrets were provided and install succeeded, pass them to the server config
        if request.secrets and result.get("success") and result.get("server_name"):
            server_name = result["server_name"]
            if server_name in mcp_manager.servers:
                server = mcp_manager.servers[server_name]
                if server.secrets is None:
                    server.secrets = {}
                server.secrets.update(request.secrets)
                mcp_manager.save_config()
                print(f"[MCP_INSTALL_DEBUG] Saved {len(request.secrets)} secrets for server '{server_name}'")
        
        print(f"[MCP_INSTALL_DEBUG] Install result: {result}")
        return result
        
    except HTTPException as he:
        print(f"[MCP_INSTALL_DEBUG] HTTPException during install: {he.status_code} {he.detail}")
        _mcp_tb.print_exc()
        raise
    except Exception as e:
        print(f"[MCP_INSTALL_DEBUG] Exception during install: {e}")
        _mcp_tb.print_exc()
        raise HTTPException(status_code=500, detail=f"MCP registry install failed: {str(e)}")

