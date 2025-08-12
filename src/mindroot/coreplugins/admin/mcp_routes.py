from fastapi import APIRouter, HTTPException
import os
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from lib.route_decorators import requires_role

# Import MCP components - prefer new mcp_ module, fallback to legacy if needed
try:
    from mindroot.coreplugins.mcp_.mod import mcp_manager, MCPServer
except ImportError:
    try:
        from mindroot.coreplugins.mcp.mod import mcp_manager, MCPServer
    except ImportError:
        # Mock objects if MCP plugin is not fully installed, to prevent startup crash
        mcp_manager = None
        MCPServer = None

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

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
    transport: str = "stdio"
    url: Optional[str] = None
    # New URL fields
    provider_url: Optional[str] = None
    transport_url: Optional[str] = None
    transport_type: Optional[str] = None  # "sse" | "streamable_http"
    # OAuth 2.0 fields
    auth_type: str = "none"
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

# --- MCP Server Management Routes ---

@router.get("/mcp/list")
async def list_mcp_servers():
    """List all configured MCP servers."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    try:
        servers = []
        for name, server in mcp_manager.servers.items():
            servers.append({
                "name": name,
                "description": server.description,
                "status": server.status,
                "transport": server.transport,
                "command": server.command,
                "args": server.args,
                "capabilities": server.capabilities
            })
        return {"success": True, "data": servers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/add")
async def add_mcp_server(server_request: McpServerAddRequest):
    """Add a new MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    try:
        # Create MCPServer object
        # Validate required fields based on transport type
        if server_request.transport == "stdio" and not server_request.command:
            raise HTTPException(status_code=400, detail="Command is required for stdio transport")
        
        if server_request.transport in ["http", "sse", "websocket"] and not server_request.url:
            raise HTTPException(status_code=400, detail="URL is required for remote transports")
        
        # More flexible OAuth validation - allow registry servers to be added without client_id initially
        # The OAuth configuration might be provided by the registry or discovered during connection
        if server_request.auth_type == "oauth2":
            # Log the OAuth configuration for debugging
            print(f"DEBUG: Adding OAuth server '{server_request.name}'")
            print(f"DEBUG: client_id: {server_request.client_id}")
            print(f"DEBUG: authorization_server_url: {server_request.authorization_server_url}")
            print(f"DEBUG: scopes: {server_request.scopes}")
            # Note: client_id validation removed to allow registry servers with dynamic OAuth discovery
        
        server = MCPServer(
            name=server_request.name,
            description=server_request.description,
            command=server_request.command or "",
            args=server_request.args,
            env=server_request.env,
            transport=server_request.transport,
            url=server_request.url,
            auth_type=server_request.auth_type,
            auth_headers=server_request.auth_headers,
            authorization_server_url=server_request.authorization_server_url,
            client_id=server_request.client_id,
            client_secret=server_request.client_secret,
            scopes=server_request.scopes,
            redirect_uri=server_request.redirect_uri or f"{server_request.url}/oauth/callback" if server_request.url else None
        )
        
        # Use BASE_URL for redirect_uri if not explicitly provided
        if not server.redirect_uri and server_request.auth_type == "oauth2":
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            server.redirect_uri = f"{base_url}/mcp_oauth_cb"
        
        mcp_manager.add_server(server_request.name, server)
        
        return {
            "success": True, 
            "message": f"MCP server '{server_request.name}' added successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/remove")
async def remove_mcp_server(request: McpServerRequest):
    """Remove an MCP server configuration."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    try:
        # First disconnect if connected
        if request.server_name in mcp_manager.sessions:
            await mcp_manager.disconnect_server(request.server_name)
        
        # Remove server configuration
        mcp_manager.remove_server(request.server_name)
        
        return {
            "success": True, 
            "message": f"MCP server '{request.server_name}' removed successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/connect")
async def connect_mcp_server(request: McpConnectRequest):
    """Connect to an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    # Persist secrets if provided
    if request.secrets:
        if request.server_name in mcp_manager.servers:
            server = mcp_manager.servers[request.server_name]
            if server.secrets is None:
                server.secrets = {}
            server.secrets.update(request.secrets)
            # This will save the updated server config, including secrets
            mcp_manager.save_config()

    try:
        success = await mcp_manager.connect_server(request.server_name, secrets=request.secrets)
        if success:
            return {
                "success": True, 
                "message": f"MCP server '{request.server_name}' connected successfully."
            }
        else:
            print(f"DEBUG: Failed to connect to MCP server '{request.server_name}'")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to connect to MCP server '{request.server_name}'. Check logs for details."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcp/disconnect")
async def disconnect_mcp_server(request: McpServerRequest):
    """Disconnect from an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    try:
        success = await mcp_manager.disconnect_server(request.server_name)
        if success:
            return {
                "success": True, 
                "message": f"MCP server '{request.server_name}' disconnected successfully."
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to disconnect from MCP server '{request.server_name}'."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
