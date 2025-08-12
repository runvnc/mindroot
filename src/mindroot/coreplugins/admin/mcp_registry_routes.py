"""MCP Registry Integration Routes

Handles browsing and installing MCP servers from the registry.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import httpx
import json
import os
from lib.route_decorators import requires_role
from lib.providers.services import service_manager

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

class RegistryServerInstallRequest(BaseModel):
    registry_id: str
    server_name: Optional[str] = None  # Override name if desired

class RegistryBrowseRequest(BaseModel):
    category: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    limit: int = 20

@router.get("/mcp/registry/browse")
async def browse_registry_servers(category: Optional[str] = None, search: Optional[str] = None, page: int = 1, limit: int = 20):
    """Browse MCP servers from the registry."""
    try:
        # Get registry settings
        registry_url = "https://registry.mindroot.io"  # Default
        registry_token = None
        
        try:
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

        # Build query parameters
        params = {
            "category": "mcp_server",
            "page": page,
            "limit": limit
        }
        
        if category:
            params["filter_category"] = category
        if search:
            params["search"] = search

        headers = {"Content-Type": "application/json"}
        if registry_token:
            headers["Authorization"] = f"Bearer {registry_token}"

        # Query registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{registry_url}/browse",
                params=params,
                headers=headers
            )

            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Registry query failed: {error_detail}"
                )

            result = response.json()
            
            # Filter and format MCP servers
            servers = []
            for item in result.get("items", []):
                if item.get("category") == "mcp_server":
                    server_data = item.get("data", {})
                    servers.append({
                        "registry_id": item.get("id"),
                        "title": item.get("title"),
                        "description": item.get("description"),
                        "version": item.get("version"),
                        "author": item.get("author"),
                        "tags": item.get("tags", []),
                        "server_type": server_data.get("server_type", "unknown"),
                        "transport": server_data.get("transport", "unknown"),
                        "url": server_data.get("url"),
                        "tools": server_data.get("tools", []),
                        "auth_type": server_data.get("auth_type", "none"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at")
                    })
            
            return {
                "success": True,
                "servers": servers,
                "total": len(servers),
                "page": page,
                "limit": limit
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registry browse failed: {str(e)}")

@router.get("/mcp/registry/server/{registry_id}")
async def get_registry_server_details(registry_id: str):
    """Get detailed information about a specific registry server."""
    try:
        # Get registry settings
        registry_url = "https://registry.mindroot.io"  # Default
        registry_token = None
        
        try:
            settings_file = 'data/registry_settings.json'
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    registry_url = settings.get("registry_url", registry_url)
                    registry_token = settings.get("registry_token")
            
            if not registry_token:
                registry_token = os.getenv('REGISTRY_TOKEN')
        except Exception as e:
            print(f"Error reading registry settings: {e}")

        headers = {"Content-Type": "application/json"}
        if registry_token:
            headers["Authorization"] = f"Bearer {registry_token}"

        # Get server details from registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{registry_url}/item/{registry_id}",
                headers=headers
            )

            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Registry server lookup failed: {error_detail}"
                )

            item = response.json()
            
            if item.get("category") != "mcp_server":
                raise HTTPException(status_code=400, detail="Item is not an MCP server")
            
            server_data = item.get("data", {})
            
            return {
                "success": True,
                "server": {
                    "registry_id": item.get("id"),
                    "title": item.get("title"),
                    "description": item.get("description"),
                    "version": item.get("version"),
                    "author": item.get("author"),
                    "tags": item.get("tags", []),
                    "server_type": server_data.get("server_type", "unknown"),
                    "transport": server_data.get("transport", "unknown"),
                    "url": server_data.get("url"),
                    "command": server_data.get("command"),
                    "args": server_data.get("args", []),
                    "env": server_data.get("env", {}),
                    "tools": server_data.get("tools", []),
                    "resources": server_data.get("resources", []),
                    "prompts": server_data.get("prompts", []),
                    "auth_type": server_data.get("auth_type", "none"),
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at")
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registry server lookup failed: {str(e)}")

@router.post("/mcp/registry/install")
async def install_registry_server(request: RegistryServerInstallRequest):
    """Install an MCP server from the registry."""
    try:
        # First get server details from registry
        server_details_response = await get_registry_server_details(request.registry_id)
        server_info = server_details_response["server"]
        
        # Determine server name
        server_name = request.server_name or server_info["title"].lower().replace(" ", "_")
        
        # Get MCP manager
        mcp_manager = await service_manager.enhanced_mcp_manager_service()
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        # Check if server already exists
        if server_name in mcp_manager.servers:
            raise HTTPException(status_code=400, detail=f"Server '{server_name}' already exists")
        
        # Create server configuration based on type
        if server_info["server_type"] == "remote":
            # Remote server - use OAuth if needed
            from mindroot.coreplugins.mcp_.mod import MCPServer
            import os
            
            # Get BASE_URL for callback
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            
            server = MCPServer(
                name=server_name,
                description=server_info["description"],
                command=None,  # Not used for remote servers
                transport="http",
                url=server_info["url"],
                auth_type=server_info.get("auth_type", "oauth2"),
                redirect_uri=f"{base_url}/mcp_oauth_cb"
            )
            
            # Add server to manager
            mcp_manager.add_server(server_name, server)
            
            # Try to connect (will handle OAuth if needed)
            success = await mcp_manager.connect_server(server_name)
            
            if not success:
                # Check if OAuth flow is pending
                oauth_status = mcp_manager.get_oauth_status(server_name)
                
                if "oauth_flow" in oauth_status and oauth_status["oauth_flow"]["status"] == "awaiting_authorization":
                    return {
                        "success": False,
                        "requires_oauth": True,
                        "auth_url": oauth_status["oauth_flow"]["auth_url"],
                        "flow_id": oauth_status["oauth_flow"]["flow_id"],
                        "server_name": server_name,
                        "message": "OAuth authorization required to complete installation."
                    }
                else:
                    # Remove failed server
                    mcp_manager.remove_server(server_name)
                    raise HTTPException(status_code=500, detail="Failed to connect to remote server")
            
            # Success - server is connected
            tools_count = len(server.capabilities.get("tools", []))
            
            # Mark as installed (will only save to config if local)
            mcp_manager.mark_server_as_installed(server_name, request.registry_id)
            is_local = mcp_manager._is_local_server(server)
            
            return {
                "success": True,
                "message": f"Successfully installed '{server_name}' with {tools_count} tools.",
                "server_name": server_name,
                "tools_count": tools_count,
                "server_type": "local" if is_local else "remote",
                "persisted": is_local,
                "installed": True
            }
            
        elif server_info["server_type"] == "local":
            # Local server - use enhanced manager for installation
            try:
                enhanced_mcp_manager = await service_manager.enhanced_mcp_manager_service()
                if not enhanced_mcp_manager:
                    raise HTTPException(status_code=500, detail="Enhanced MCP manager service not available")
                
                from mindroot.coreplugins.mcp_.mod import MCPServer
                
                # Create enhanced server configuration
                enhanced_server = MCPServer(                    name=server_name,
                    description=server_info["description"],
                    command=server_info["command"],
                    args=server_info.get("args", []),
                    env=server_info.get("env", {}),
                    install_method="manual",  # Registry servers are pre-configured
                    auto_install=False
                )
                
                # Add to enhanced manager
                enhanced_mcp_manager.add_server(server_name, enhanced_server)
                
                # Connect to server
                success = await enhanced_mcp_manager.connect_server(server_name)
                
                if not success:
                    enhanced_mcp_manager.remove_server(server_name)
                    raise HTTPException(status_code=500, detail="Failed to connect to local server")
                
                # Get tools count
                server = enhanced_mcp_manager.servers[server_name]
                tools_count = len(server.capabilities.get("tools", []))
                
                # Mark as installed (will only save to config if local)
                enhanced_mcp_manager.mark_server_as_installed(server_name, request.registry_id)
                is_local = enhanced_mcp_manager._is_local_server(server)
                
                return {
                    "success": True,
                    "message": f"Successfully installed '{server_name}' with {tools_count} tools.",
                    "server_name": server_name,
                    "tools_count": tools_count,
                    "server_type": "local" if is_local else "remote",
                    "persisted": is_local,
                    "installed": True
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Local server installation failed: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported server type: {server_info['server_type']}")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Registry server installation failed: {str(e)}")

@router.post("/mcp/registry/complete-oauth")
async def complete_registry_oauth(server_name: str, code: str, state: Optional[str] = None):
    """Complete OAuth flow for registry server installation."""
    try:
        # Get the MCP manager service
        mcp_manager = await service_manager.enhanced_mcp_manager_service()
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        # Complete the OAuth flow
        success = mcp_manager.complete_oauth_flow(server_name, code, state)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to complete OAuth flow")
        
        # Wait a moment for the OAuth flow to complete
        import asyncio
        await asyncio.sleep(1)
        
        # Check if server is now connected
        if server_name in mcp_manager.servers:
            server = mcp_manager.servers[server_name]
            if server.status == "connected":
                tools = server.capabilities.get("tools", [])
                resources = server.capabilities.get("resources", [])
                prompts = server.capabilities.get("prompts", [])
                
                return {
                    "success": True,
                    "message": f"OAuth completed successfully. Registry server '{server_name}' installed with {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts.",
                    "server_name": server_name,
                    "tools_count": len(tools),
                    "resources_count": len(resources),
                    "prompts_count": len(prompts)
                }
        
        return {
            "success": True,
            "message": "OAuth flow completed, but server connection is still pending.",
            "server_name": server_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OAuth completion failed: {str(e)}")

@router.get("/mcp/registry/installation-status")
async def get_installation_status():
    """Get installation status of all registry servers."""
    try:
        mcp_manager = await service_manager.enhanced_mcp_manager_service()
        if not mcp_manager:
            return {"success": False, "installed_servers": []}
        
        installed_servers = []
        for name, server in mcp_manager.servers.items():
            # Include servers with registry_id OR servers that are marked as installed
            has_registry_id = hasattr(server, 'registry_id') and server.registry_id
            is_installed = hasattr(server, 'installed') and server.installed
            
            if has_registry_id or is_installed:
                installed_servers.append({
                    "registry_id": getattr(server, 'registry_id', None),
                    "server_name": name,
                    "status": server.status,
                    "server_type": "local" if mcp_manager._is_local_server(server) else "remote",
                    "persisted": mcp_manager._is_local_server(server),
                    "tools_count": len(server.capabilities.get("tools", []))
                })
        
        return {"success": True, "installed_servers": installed_servers}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "installed_servers": [], "error": str(e)}

@router.get("/mcp/registry/categories")
async def get_registry_categories():
    """Get available MCP server categories from the registry."""
    try:
        # Get registry settings
        registry_url = "https://registry.mindroot.io"  # Default
        registry_token = None
        
        try:
            settings_file = 'data/registry_settings.json'
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    registry_url = settings.get("registry_url", registry_url)
                    registry_token = settings.get("registry_token")
            
            if not registry_token:
                registry_token = os.getenv('REGISTRY_TOKEN')
        except Exception as e:
            print(f"Error reading registry settings: {e}")

        headers = {"Content-Type": "application/json"}
        if registry_token:
            headers["Authorization"] = f"Bearer {registry_token}"

        # Get categories from registry
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{registry_url}/categories",
                headers=headers
            )

            if response.status_code >= 400:
                # Fallback to default categories if endpoint doesn't exist
                return {
                    "success": True,
                    "categories": ["utilities", "development", "database", "communication", "ai", "automation"]
                }

            result = response.json()
            return {
                "success": True,
                "categories": result.get("categories", [])
            }

    except Exception as e:
        # Fallback to default categories
        return {
            "success": True,
            "categories": ["utilities", "development", "database", "communication", "ai", "automation"]
        }

@router.post("/mcp/registry/mark-installed")
async def mark_server_installed(server_name: str, registry_id: str = None):
    """Manually mark a server as installed (for testing/fixing)."""
    try:
        mcp_manager = await service_manager.enhanced_mcp_manager_service()
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager service not available")
        
        if server_name not in mcp_manager.servers:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")
        
        mcp_manager.mark_server_as_installed(server_name, registry_id)
        
        return {
            "success": True,
            "message": f"Server '{server_name}' marked as installed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))