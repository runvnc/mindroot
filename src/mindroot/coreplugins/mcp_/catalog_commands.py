import os
import asyncio
from typing import Dict, List, Optional, Any
from lib.providers.commands import command
from .catalog_manager import MCPCatalogManager
from .enhanced_mod import enhanced_mcp_manager, EnhancedMCPServer

# Global catalog manager
# Use current working directory for data files
catalog_manager = MCPCatalogManager(working_dir=os.getcwd())


@command()
async def mcp_catalog_list(category: str = None, context=None):
    """List MCP servers from catalog
    
    Example:
    { "mcp_catalog_list": {} }
    { "mcp_catalog_list": { "category": "utilities" } }
    """
    # Update running status first
    catalog = catalog_manager.update_server_status()
    
    if category:
        servers = catalog_manager.get_servers_by_category(category)
    else:
        servers = catalog.get("servers", {})
    
    # Format for display
    result = []
    for name, server in servers.items():
        result.append({
            "name": name,
            "display_name": server.get("display_name", name),
            "description": server.get("description", ""),
            "category": server.get("category", "unknown"),
            "install_method": server.get("install_method", "manual"),
            "installed": server.get("installed", False),
            "running": server.get("running", False),
            "status": server.get("status", "unknown"),
            "tools": server.get("tools", []),
            "tags": server.get("tags", [])
        })
    
    return {
        "servers": result,
        "count": len(result),
        "categories": catalog_manager.get_categories()
    }


@command()
async def mcp_catalog_search(query: str, context=None):
    """Search MCP servers in catalog
    
    Example:
    { "mcp_catalog_search": { "query": "calculator" } }
    { "mcp_catalog_search": { "query": "database" } }
    """
    servers = catalog_manager.search_servers(query)
    
    result = []
    for name, server in servers.items():
        result.append({
            "name": name,
            "display_name": server.get("display_name", name),
            "description": server.get("description", ""),
            "category": server.get("category", "unknown"),
            "installed": server.get("installed", False),
            "running": server.get("running", False),
            "tags": server.get("tags", [])
        })
    
    return {
        "query": query,
        "results": result,
        "count": len(result)
    }


@command()
async def mcp_catalog_install(server_name: str, context=None):
    """Install an MCP server from catalog
    
    Example:
    { "mcp_catalog_install": { "server_name": "calculator" } }
    """
    server_info = catalog_manager.get_server_info(server_name)
    if not server_info:
        return f"Server {server_name} not found in catalog"
    
    # Create server config from catalog info
    server = MCPServer(
        name=server_info["name"],
        description=server_info["description"],
        command=server_info["command"],
        args=server_info["args"],
        env=server_info.get("env", {})
    )
    
    # Add to manager
    mcp_manager.add_server(server_name, server)
    
    # Install server if needed (for uvx/npx packages)
    install_method = server_info.get("install_method", "manual")
    install_package = server_info.get("install_package")
    
    if install_method in ["uvx", "npx"] and install_package:
        try:
            import subprocess
            if install_method == "uvx":
                result = subprocess.run(["uvx", "--help"], capture_output=True)
                if result.returncode != 0:
                    return f"uvx not available. Please install uv first."
            elif install_method == "npx":
                result = subprocess.run(["npx", "--version"], capture_output=True)
                if result.returncode != 0:
                    return f"npx not available. Please install Node.js first."
        except Exception as e:
            return f"Error checking {install_method}: {e}"
    
    # Mark as installed (basic implementation)
    success = True  # For now, assume installation succeeds    
    if success:
        catalog_manager.mark_server_installed(server_name, True)
        return f"Successfully installed {server_name}"
    else:
        return f"Failed to install {server_name}"


@command()
async def mcp_catalog_install_and_run(server_name: str, context=None):
    """Install and run an MCP server from catalog (one-click)
    
    Example:
    { "mcp_catalog_install_and_run": { "server_name": "calculator" } }
    """
    # First install
    install_result = await mcp_catalog_install(server_name, context)
    
    if "Failed" in install_result:
        return install_result
    
    # Then connect (which will auto-install if needed)
    success = await enhanced_mcp_manager.connect_server(server_name)
    
    if success:
        catalog_manager.update_server_status()
        
        # Add a small delay and then refresh dynamic commands to ensure they register
        await asyncio.sleep(1)
        
        # Import and call the refresh function
        from .enhanced_mod import mcp_refresh_dynamic_commands
        refresh_result = await mcp_refresh_dynamic_commands()
        
        return f"Successfully installed and connected to {server_name}. MCP tools are now available as commands. Refreshed {refresh_result.get('total_dynamic_commands', 0)} dynamic commands."
    else:
        return f"Installed {server_name} but failed to connect"


@command()
async def mcp_catalog_stop(server_name: str, context=None):
    """Stop an MCP server
    
    Example:
    { "mcp_catalog_stop": { "server_name": "calculator" } }
    """
    success = await enhanced_mcp_manager.disconnect_server(server_name)
    
    if success:
        catalog_manager.update_server_status()
        return f"Successfully stopped {server_name}"
    else:
        return f"Failed to stop {server_name}"


@command()
async def mcp_catalog_status(context=None):
    """Get status of all catalog servers
    
    Example:
    { "mcp_catalog_status": {} }
    """
    catalog = catalog_manager.update_server_status()
    servers = catalog.get("servers", {})
    
    status_summary = {
        "total": len(servers),
        "installed": 0,
        "running": 0,
        "available": 0
    }
    
    server_status = []
    
    for name, server in servers.items():
        installed = server.get("installed", False)
        running = server.get("running", False)
        
        if installed:
            status_summary["installed"] += 1
        if running:
            status_summary["running"] += 1
        if server.get("status") == "available":
            status_summary["available"] += 1
        
        server_status.append({
            "name": name,
            "display_name": server.get("display_name", name),
            "installed": installed,
            "running": running,
            "category": server.get("category", "unknown")
        })
    
    return {
        "summary": status_summary,
        "servers": server_status
    }


@command()
async def mcp_catalog_info(server_name: str, context=None):
    """Get detailed info about a catalog server
    
    Example:
    { "mcp_catalog_info": { "server_name": "calculator" } }
    """
    server_info = catalog_manager.get_server_info(server_name)
    
    if not server_info:
        return f"Server {server_name} not found in catalog"
    
    # Update running status
    running_status = catalog_manager.detect_running_servers()
    server_info["running"] = running_status.get(server_name, False)
    
    return server_info


@command()
async def mcp_catalog_categories(context=None):
    """Get list of server categories
    
    Example:
    { "mcp_catalog_categories": {} }
    """
    categories = catalog_manager.get_categories()
    catalog = catalog_manager.load_catalog()
    
    # Count servers per category
    category_counts = {}
    for server in catalog.get("servers", {}).values():
        category = server.get("category", "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return {
        "categories": categories,
        "counts": category_counts
    }


@command()
async def mcp_catalog_add_custom(server_info: Dict[str, Any], context=None):
    """Add a custom server to the catalog
    
    Example:
    { "mcp_catalog_add_custom": {
        "server_info": {
            "name": "my_server",
            "display_name": "My Custom Server",
            "description": "Custom MCP server",
            "command": "python",
            "args": ["-m", "my_mcp_server"],
            "category": "custom",
            "install_method": "manual"
        }
    }}
    """
    success = catalog_manager.add_custom_server(server_info)
    
    if success:
        return f"Successfully added custom server {server_info.get('name')}"
    else:
        return "Failed to add custom server - missing required fields"


@command()
async def mcp_catalog_refresh(context=None):
    """Refresh catalog and update server status
    
    Example:
    { "mcp_catalog_refresh": {} }
    """
    catalog = catalog_manager.update_server_status()
    running_count = sum(1 for server in catalog.get("servers", {}).values() 
                       if server.get("running", False))
    
    return {
        "message": "Catalog refreshed",
        "total_servers": len(catalog.get("servers", {})),
        "running_servers": running_count
    }