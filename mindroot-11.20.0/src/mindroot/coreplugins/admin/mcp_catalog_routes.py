from fastapi import APIRouter, HTTPException
from typing import Optional
from lib.route_decorators import requires_role

# Import MCP components - use the actual MCP system
try:
    from mindroot.coreplugins.mcp.mod import mcp_manager, MCPServer
    from mindroot.coreplugins.mcp.catalog_manager import MCPCatalogManager
except ImportError:
    # Mock objects if MCP plugin is not fully installed, to prevent startup crash
    mcp_manager = None
    MCPServer = None
    MCPCatalogManager = None

# Create router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

# --- MCP Catalog/Directory Routes ---

@router.get("/mcp/catalog")
async def get_mcp_catalog():
    """Get the MCP server catalog/directory."""
    if not MCPCatalogManager:
        raise HTTPException(status_code=501, detail="MCP Catalog not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        catalog = catalog_manager.load_catalog()
        
        # Update running status
        catalog_manager.update_server_status()
        
        return {
            "success": True, 
            "data": catalog
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/catalog/search")
async def search_mcp_catalog(query: str = "", category: Optional[str] = None):
    """Search the MCP server catalog."""
    if not MCPCatalogManager:
        raise HTTPException(status_code=501, detail="MCP Catalog not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        
        if query:
            results = catalog_manager.search_servers(query)
        elif category:
            results = catalog_manager.get_servers_by_category(category)
        else:
            catalog = catalog_manager.load_catalog()
            results = catalog.get("servers", {})
        
        return {
            "success": True, 
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/catalog/categories")
async def get_mcp_categories():
    """Get available MCP server categories."""
    if not MCPCatalogManager:
        raise HTTPException(status_code=501, detail="MCP Catalog not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        categories = catalog_manager.get_categories()
        
        return {
            "success": True, 
            "data": categories
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/catalog/install")
async def install_from_catalog(server_name: str):
    """Install an MCP server from the catalog."""
    if not MCPCatalogManager or not mcp_manager:
        raise HTTPException(status_code=501, detail="MCP system not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        server_info = catalog_manager.get_server_info(server_name)
        
        if not server_info:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found in catalog")
        
        # Create MCPServer object from catalog info
        server = MCPServer(
            name=server_name,
            description=server_info.get("description", ""),
            command=server_info.get("command", ""),
            args=server_info.get("args", []),
            env=server_info.get("env", {}),
            transport=server_info.get("transport", "stdio"),
            url=server_info.get("url")
        )
        
        # Add to MCP manager
        mcp_manager.add_server(server_name, server)
        
        # Mark as installed in catalog
        catalog_manager.mark_server_installed(server_name, True)
        
        return {
            "success": True, 
            "message": f"MCP server '{server_name}' installed from catalog successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/catalog/server/{server_name}")
async def get_catalog_server_info(server_name: str):
    """Get detailed information about a specific server from the catalog."""
    if not MCPCatalogManager:
        raise HTTPException(status_code=501, detail="MCP Catalog not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        server_info = catalog_manager.get_server_info(server_name)
        
        if not server_info:
            raise HTTPException(status_code=404, detail=f"MCP server '{server_name}' not found in catalog")
        
        return {
            "success": True, 
            "data": server_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/catalog/refresh")
async def refresh_catalog_status():
    """Refresh the running status of all servers in the catalog."""
    if not MCPCatalogManager:
        raise HTTPException(status_code=501, detail="MCP Catalog not available")
    
    try:
        catalog_manager = MCPCatalogManager()
        updated_catalog = catalog_manager.update_server_status()
        
        return {
            "success": True, 
            "message": "Catalog status refreshed successfully.",
            "data": updated_catalog
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
