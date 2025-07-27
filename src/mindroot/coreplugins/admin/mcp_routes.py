from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from lib.route_decorators import requires_role

# Import MCP components - use the actual MCP system
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

class McpServerRequest(BaseModel):
    server_name: str

class McpServerAddRequest(BaseModel):
    name: str
    description: str
    command: str
    args: List[str] = []
    env: dict = {}
    transport: str = "stdio"
    url: Optional[str] = None

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
        server = MCPServer(
            name=server_request.name,
            description=server_request.description,
            command=server_request.command,
            args=server_request.args,
            env=server_request.env,
            transport=server_request.transport,
            url=server_request.url
        )
        
        # Add server to manager
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
async def connect_mcp_server(request: McpServerRequest):
    """Connect to an MCP server."""
    if not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP Plugin not available")
    
    try:
        success = await mcp_manager.connect_server(request.server_name)
        if success:
            return {
                "success": True, 
                "message": f"MCP server '{request.server_name}' connected successfully."
            }
        else:
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
