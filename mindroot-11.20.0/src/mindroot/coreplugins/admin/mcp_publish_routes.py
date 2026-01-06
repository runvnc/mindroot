from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from lib.route_decorators import requires_role
from lib.providers.services import service_manager
import httpx
import json
import uuid
import asyncio

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

class McpTestRemoteRequest(BaseModel):
    url: str
    name: Optional[str] = None

class McpTestLocalRequest(BaseModel):
    name: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}

class McpCompleteOAuthRequest(BaseModel):
    server_name: str
    code: str
    state: Optional[str] = None

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

        # Prepare registry publish data
        publish_data = {
            "title": request.name,
            "description": request.description,
            "category": "mcp_server",
            "content_type": "mcp_server",
            "version": "1.0.0",
            "tags": ["mcp", "server", request.server_type],
            "dependencies": []
        }

        # Prepare server data for registry
        server_data = {
            "name": request.name,
            "description": request.description,
            "transport": "stdio" if request.server_type == 'local' else "http",
            "auth_type": "none" if request.server_type == 'local' else "auto",
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
                "url": request.url
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

@router.post("/mcp/test-local")
async def test_local_mcp_server(request: McpTestLocalRequest):
    """Test connection to a local MCP server and list its capabilities."""
    try:
        # Get the MCP manager service
        mcp_manager = await service_manager.enhanced_mcp_manager_service(context=None)
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        print(f"DEBUG: test_local_mcp_server: Testing local server {request.name} with command {request.command}")
        
        # Use the new testing method from MCPManager
        result = await mcp_manager.test_local_server_capabilities(
            name=request.name,
            command=request.command,
            args=request.args,
            env=request.env
        )
        
        print(f"DEBUG: test_local_mcp_server: Result: {result}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Local server test failed: {str(e)}")

@router.post("/mcp/test-remote")
async def test_remote_mcp_server(request: McpTestRemoteRequest):
    """Test connection to a remote MCP server and list its tools using MCP manager OAuth flow."""
    try:
        # Get the MCP manager service
        print("Testing remote MCP server connection: ", request.url)
        mcp_manager = await service_manager.enhanced_mcp_manager_service(context=None)
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        # Generate a unique temporary server name
        temp_server_name = f"temp_publish_test_{uuid.uuid4().hex[:8]}"
        server_name = request.name or temp_server_name
        print(f"Using server name: {server_name}")

        try:
            from mindroot.coreplugins.mcp_.mod import MCPServer
            
            # Check if server already exists (from registry install flow)
            existing_server = None
            if server_name in mcp_manager.servers:
                existing_server = mcp_manager.servers[server_name]
                print(f"Found existing server configuration for {server_name}")
                print(f"Existing server auth_type: {existing_server.auth_type}")
                print(f"Existing server client_id: {existing_server.client_id}")
            
            if existing_server:
                # Use existing server configuration (registry install flow)
                server_to_test = existing_server
                print(f"Using existing server config with auth_type={server_to_test.auth_type}")
            else:
                # Create temporary server configuration for testing (publish flow)
                temp_server = MCPServer(
                    name=server_name,
                    description=f"Temporary server for testing {request.url}",
                    command="",  # Not used for remote servers
                    transport="http",
                    url=request.url,
                    auth_type="oauth2"  # Assume OAuth2 for remote servers
                )
                
                # Add temporary server to MCP manager
                mcp_manager.add_server(server_name, temp_server)
                server_to_test = temp_server
                print(f"Created temporary server config for publish flow")
            
            # Note: OAuth client_id will be discovered during the OAuth flow
            
            print("Connecting to remote MCP server: ", server_name)
            print(f"Server URL: {request.url}")
            print("MCP manager is: ", mcp_manager)
            mcp_manager = await service_manager.enhanced_mcp_manager_service(context=None)
            print("MCP manager after re-fetch: ", mcp_manager)

            print("Running sanity test")
            await mcp_manager.sanity_test()
            # Try to connect (this will handle OAuth flow if needed)
            success = await mcp_manager.connect_server(server_name)
            print("Connection result: ", success)
            if not success:
                # Check if OAuth flow is pending
                oauth_status = mcp_manager.get_oauth_status(server_name)
                
                if "oauth_flow" in oauth_status and oauth_status["oauth_flow"]["status"] == "awaiting_authorization":
                    # OAuth flow is pending - return the auth URL for frontend to handle
                    return {
                        "success": False,
                        "requires_oauth": True,
                        "auth_url": oauth_status["oauth_flow"]["auth_url"],
                        "flow_id": oauth_status["oauth_flow"]["flow_id"],
                        "server_name": server_name,
                        "message": "OAuth authorization required. Please complete the authorization flow."
                    }
                else:
                    # Try without OAuth first to see if it's a 401
                    try:
                        await test_direct_connection(request.url)
                    except HTTPException as e:
                        if e.status_code == 401:
                            # Server requires auth - try OAuth connection
                            oauth_success = await mcp_manager.connect_oauth_server(server_name)
                            if not oauth_success:
                                oauth_status = mcp_manager.get_oauth_status(server_name)
                                if "oauth_flow" in oauth_status:
                                    return {
                                        "success": False,
                                        "requires_oauth": True,
                                        "auth_url": oauth_status["oauth_flow"]["auth_url"],
                                        "flow_id": oauth_status["oauth_flow"]["flow_id"],
                                        "server_name": server_name,
                                        "message": "OAuth authorization required. Please complete the authorization flow."
                                    }
                        raise e
            
            # Get server capabilities (tools, resources, prompts)
            server = mcp_manager.servers[server_name]
            tools = server.capabilities.get("tools", [])
            resources = server.capabilities.get("resources", [])
            prompts = server.capabilities.get("prompts", [])
            
            return {
                "success": True,
                "message": f"Successfully connected to remote MCP server. Found {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts.",
                "tools": tools,
                "resources": resources,
                "prompts": prompts,
                "server_name": server_name
            }
            
        finally:
            # Clean up temporary server
            try:
                # Only clean up if we created a temporary server (not existing one)
                if not existing_server:
                    await mcp_manager.disconnect_server(server_name)
                    mcp_manager.remove_server(server_name)
                    print(f"Cleaned up temporary server {server_name}")
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary server {server_name}: {cleanup_error}")

    except HTTPException:
        print("HTTPException occurred during MCP server test.")
        import traceback
        traceback.print_exc() 
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

async def test_direct_connection(url: str):
    """Test direct connection to MCP server without OAuth to check if auth is required."""
    headers = {
        "Content-Type": "application/json"
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
        
        if init_response.status_code == 401:
            raise HTTPException(status_code=401, detail="Server requires authentication")
        
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
        return tools

@router.post("/mcp/complete-oauth")
async def complete_oauth_flow(request: McpCompleteOAuthRequest):
    """Complete OAuth flow for MCP server testing."""
    try:
        # Get the enhanced MCP manager service
        mcp_manager = await service_manager.enhanced_mcp_manager_service(context=None)
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        # Complete the OAuth flow
        success = mcp_manager.complete_oauth_flow(request.server_name, request.code, request.state)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete OAuth flow")
        
        # Wait a bit longer for the background task to complete the connection
        await asyncio.sleep(6)
        
        # Check if server is now connected
        if request.server_name in mcp_manager.servers:
            server = mcp_manager.servers[request.server_name]
            print(f"DEBUG: complete-oauth: server entry found for '{request.server_name}', status={server.status}, tools={len(server.capabilities.get('tools', []))}")
            if server.status == "connected":
                tools = server.capabilities.get("tools", [])
                resources = server.capabilities.get("resources", [])
                prompts = server.capabilities.get("prompts", [])

                return {
                    "success": True,
                    "message": f"OAuth completed successfully. Found {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts.",
                    "tools": tools,
                    "resources": resources,
                    "prompts": prompts
                }

            # Not yet connected; surface pending status so frontend can poll
            try:
                status = mcp_manager.get_oauth_status(request.server_name)
                print(f"DEBUG: complete-oauth: oauth-status for '{request.server_name}' -> {status}")
            except Exception:
                status = {"status": "pending"}
            return {
                "success": True,
                "message": "OAuth flow completed, but server connection is still pending.",
                "status": status.get("status", "pending")
            }

        
        return {
            "success": True,
            "message": "OAuth flow completed, but server connection is still pending.",
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OAuth completion failed: {str(e)}")

@router.get("/mcp/oauth-status/{server_name}")
async def get_oauth_status(server_name: str):
    """Get OAuth flow status for a server."""
    try:
        # Get the enhanced MCP manager service
        mcp_manager = await service_manager.enhanced_mcp_manager_service(context=None)
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        status = mcp_manager.get_oauth_status(server_name)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get OAuth status: {str(e)}")
