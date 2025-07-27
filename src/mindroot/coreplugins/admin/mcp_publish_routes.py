from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from lib.route_decorators import requires_role
import httpx
import json

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

class McpServerPublishRequest(BaseModel):
    name: str
    description: str
    server_type: str  # 'local' or 'remote'
    tools: List[Dict[str, Any]]
    # Local server fields
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    # Remote server fields
    url: Optional[str] = None
    auth_headers: Optional[Dict[str, str]] = None

@router.post("/mcp/publish")
async def publish_mcp_server(request: McpServerPublishRequest):
    """Publish an MCP server to the registry."""
    try:
        # Validate request based on server type
        if request.server_type == 'local':
            if not request.command:
                raise HTTPException(status_code=400, detail="Command is required for local servers")
        elif request.server_type == 'remote':
            if not request.url:
                raise HTTPException(status_code=400, detail="URL is required for remote servers")
        else:
            raise HTTPException(status_code=400, detail="Server type must be 'local' or 'remote'")

        # Prepare server data for registry
        server_data = {
            "name": request.name,
            "description": request.description,
            "transport": "stdio" if request.server_type == 'local' else "http",
            "tools": request.tools,
            "server_type": request.server_type
        }

        # Add type-specific configuration
        if request.server_type == 'local':
            server_data.update({
                "command": request.command,
                "args": request.args or [],
                "env": request.env or {}
            })
        else:
            server_data.update({
                "url": request.url,
                "auth_headers": request.auth_headers or {}
            })

        # Prepare registry publish data
        publish_data = {
            "title": request.name,
            "description": request.description,
            "category": "mcp_server",
            "content_type": "mcp_server",
            "version": "1.0.0",
            "data": server_data,
            "tags": ["mcp", "server", request.server_type],
            "dependencies": []
        }

        # Get registry settings
        registry_url = "https://registry.mindroot.io"  # Default
        registry_token = None
        
        try:
            import os
            settings_file = 'data/registry_settings.json'
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    registry_url = settings.get("registry_url", registry_url)
                    registry_token = settings.get("registry_token")
            
            # Try environment variable if no token in file
            if not registry_token:
                registry_token = os.getenv('REGISTRY_TOKEN')
        except Exception as e:
            print(f"Error reading registry settings: {e}")

        if not registry_token:
            raise HTTPException(
                status_code=401, 
                detail="Registry authentication token not configured. Please set REGISTRY_TOKEN or configure in registry settings."
            )

        # Publish to registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{registry_url}/publish",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {registry_token}"
                },
                json=publish_data
            )

            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Registry publishing failed: {error_detail}"
                )

            result = response.json()
            return {
                "success": True,
                "message": f"MCP Server '{request.name}' published successfully!",
                "data": result
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/test-remote")
async def test_remote_mcp_server(url: str, auth_headers: Optional[Dict[str, str]] = None):
    """Test connection to a remote MCP server and list its tools."""
    try:
        headers = {
            "Content-Type": "application/json",
            **(auth_headers or {})
        }

        # Initialize connection
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "mindroot-tester",
                    "version": "1.0.0"
                }
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            init_response = await client.post(url, headers=headers, json=init_request)
            
            if init_response.status_code != 200:
                raise HTTPException(
                    status_code=init_response.status_code,
                    detail=f"Failed to initialize: {init_response.text}"
                )

            # List tools
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            tools_response = await client.post(url, headers=headers, json=tools_request)
            
            if tools_response.status_code != 200:
                raise HTTPException(
                    status_code=tools_response.status_code,
                    detail=f"Failed to list tools: {tools_response.text}"
                )

            tools_data = tools_response.json()
            tools = tools_data.get("result", {}).get("tools", [])

            return {
                "success": True,
                "message": f"Successfully connected to remote MCP server. Found {len(tools)} tools.",
                "tools": tools
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
