import asyncio
import os
import json
from urllib.parse import parse_qs, urlparse
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack

import httpx
from pydantic import BaseModel

from lib.providers.commands import command
from lib.providers.services import service
from .mcp_manager import MCPManager, MCPServer
from .server_installer import MCPServerInstaller
from .dynamic_commands import MCPDynamicCommands
from .oauth_storage import MCPTokenStorage

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.sse import sse_client
    from mcp.client.auth import OAuthClientProvider, TokenStorage
    from mcp.shared.auth import OAuthClientMetadata, OAuthToken, OAuthClientInformationFull
    from pydantic import AnyUrl
    MCP_AVAILABLE = True
except ImportError:
    # MCP not installed yet
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
    streamablehttp_client = None
    sse_client = None
    OAuthClientProvider = None
    OAuthClientMetadata = None
    OAuthToken = None
    OAuthClientInformationFull = None
    AnyUrl = None
    MCP_AVAILABLE = False

async def handle_redirect(auth_url: str) -> None:
    print(f"Visit: {auth_url}")


async def handle_callback() -> tuple[str, str | None]:
    callback_url = input("Paste callback URL: ")
    params = parse_qs(urlparse(callback_url).query)
    return params["code"][0], params.get("state", [None])[0]


# Global MCP manager instance
mcp_manager = MCPManager()


@service()
async def mcp_manager_service(context=None):
    """Service to access the MCP manager"""
    print("returning mcp_manager")
    return mcp_manager

@service()
async def enhanced_mcp_manager_service(context=None):
    """Service to access enhanced MCP manager (same as mcp_manager_service now)"""
    print("returning enhanced MCP manager service")
    return mcp_manager


@command()
async def mcp_connect(server_name: str, context=None):
    """Connect to an MCP server
    
    Example:
    { "mcp_connect": { "server_name": "filesystem" } }
    """
    success = await mcp_manager.connect_server(server_name)
    if success:
        return f"Successfully connected to MCP server: {server_name}"
    else:
        return f"Failed to connect to MCP server: {server_name}"


@command()
async def mcp_disconnect(server_name: str, context=None):
    """Disconnect from an MCP server
    
    Example:
    { "mcp_disconnect": { "server_name": "filesystem" } }
    """
    success = await mcp_manager.disconnect_server(server_name)
    if success:
        return f"Successfully disconnected from MCP server: {server_name}"
    else:
        return f"Failed to disconnect from MCP server: {server_name}"


@command()
async def mcp_list_servers(context=None):
    """List all configured MCP servers
    
    Example:
    { "mcp_list_servers": {} }
    """
    servers = []
    for name, server in mcp_manager.servers.items():
        servers.append({
            "name": name,
            "description": server.description,
            "status": server.status,
            "transport": server.transport,
            "tools_count": len(server.capabilities.get("tools", [])),
            "resources_count": len(server.capabilities.get("resources", [])),
            "prompts_count": len(server.capabilities.get("prompts", []))
        })
    return servers


# Enhanced commands from enhanced_mod.py
@command()
async def mcp_enhanced_connect(server_name: str, context=None):
    """Connect to MCP server with enhanced features
    
    Example:
    { "mcp_enhanced_connect": { "server_name": "calculator" } }
    """
    success = await mcp_manager.connect_server(server_name)
    if success:
        return f"Successfully connected to {server_name} with enhanced features"
    else:
        return f"Failed to connect to {server_name}"


@command()
async def mcp_enhanced_disconnect(server_name: str, context=None):
    """Disconnect from MCP server
    
    Example:
    { "mcp_enhanced_disconnect": { "server_name": "calculator" } }
    """
    success = await mcp_manager.disconnect_server(server_name)
    if success:
        return f"Successfully disconnected from {server_name}"
    else:
        return f"Failed to disconnect from {server_name}"


@command()
async def mcp_install_uvx_server(name: str, package: str, description: str = None, context=None):
    """Install and configure a uvx-based MCP server
    
    Example:
    { "mcp_install_uvx_server": {
        "name": "calculator",
        "package": "mcp-server-calculator",
        "description": "Calculator server"
    } }
    """
    server = MCPServer(
        name=name,
        description=description or f"MCP server: {name}",
        command="uvx",
        args=[package],
        install_method="uvx",
        install_package=package,
        auto_install=True
    )
    
    mcp_manager.add_server(name, server)
    return f"Configured uvx server {name} with package {package}"


@command()
async def mcp_install_npx_server(name: str, package: str, description: str = None, context=None):
    """Install and configure an npx-based MCP server
    
    Example:
    { "mcp_install_npx_server": {
        "name": "github",
        "package": "@modelcontextprotocol/server-github",
        "description": "GitHub server"
    } }
    """
    server = MCPServer(
        name=name,
        description=description or f"MCP server: {name}",
        command="npx",
        args=["-y", package],
        install_method="npx",
        install_package=package,
        auto_install=True
    )
    
    mcp_manager.add_server(name, server)
    return f"Configured npx server {name} with package {package}"


@command()
async def mcp_debug_connection(server_name: str, context=None):
    """Debug MCP server connection and dynamic command registration
    
    Example:
    { "mcp_debug_connection": { "server_name": "calculator" } }
    { "mcp_debug_connection": { "server_name": "github" } }
    """
    from .catalog_commands import mcp_catalog_info, mcp_catalog_install_and_run
    from lib.providers.commands import command_manager
    import json
    
    debug_info = {
        "server_name": server_name,
        "steps": []
    }
    
    # Step 1: Check initial state
    initial_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    debug_info["steps"].append({
        "step": "1_initial_state",
        "initial_mcp_commands_count": len(initial_commands),
        "dynamic_commands": mcp_manager.dynamic_commands.get_registered_commands()
    })
    
    # Step 2: Get server info
    try:
        server_info = await mcp_catalog_info(server_name)
        debug_info["steps"].append({
            "step": "2_server_info",
            "success": True,
            "server_info": server_info
        })
    except Exception as e:
        debug_info["steps"].append({
            "step": "2_server_info",
            "success": False,
            "error": str(e)
        })
        return debug_info
    
    # Step 3: Install and run
    try:
        result = await mcp_catalog_install_and_run(server_name)
        debug_info["steps"].append({
            "step": "3_install_and_run",
            "success": True,
            "result": result
        })
    except Exception as e:
        debug_info["steps"].append({
            "step": "3_install_and_run",
            "success": False,
            "error": str(e)
        })
        return debug_info
    
    # Step 4: Check server status
    server_status = {}
    if server_name in mcp_manager.servers:
        server = mcp_manager.servers[server_name]
        server_status = {
            "status": server.status,
            "capabilities": server.capabilities,
            "has_session": server_name in mcp_manager.sessions
        }
    
    debug_info["steps"].append({
        "step": "4_server_status",
        "server_found": server_name in mcp_manager.servers,
        "server_status": server_status
    })
    
    # Step 5: Check dynamic commands
    final_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    new_commands = [cmd for cmd in final_commands if cmd not in initial_commands]
    
    debug_info["steps"].append({
        "step": "5_dynamic_commands",
        "total_mcp_commands": len(final_commands),
        "new_commands": new_commands,
        "dynamic_commands_tracker": mcp_manager.dynamic_commands.get_registered_commands()
    })
    
    # Step 6: Analyze tools
    if server_name in mcp_manager.servers:
        server = mcp_manager.servers[server_name]
        tools = server.capabilities.get('tools', [])
        tool_analysis = []
        
        for tool in tools:
            tool_name = tool.get('name', 'unknown')
            #expected_cmd = f"mcp_{server_name}_{tool_name}"
            expecte_cmd = "mcp_"+tool_name
            is_registered = expected_cmd in command_manager.functions
            tool_analysis.append({
                "tool_name": tool_name,
                "expected_command": expected_cmd,
                "is_registered": is_registered,
                "tool_details": tool
            })
        
        debug_info["steps"].append({
            "step": "6_tool_analysis",
            "tools_count": len(tools),
            "tool_analysis": tool_analysis
        })
    
    # Step 7: Manual verification if session exists
    if server_name in mcp_manager.sessions:
        try:
            session = mcp_manager.sessions[server_name]
            tools_result = await session.list_tools()
            debug_info["steps"].append({
                "step": "7_manual_verification",
                "success": True,
                "direct_tools_count": len(tools_result.tools),
                "direct_tools": [{
                    "name": tool.name,
                    "description": tool.description
                } for tool in tools_result.tools]
            })
        except Exception as e:
            debug_info["steps"].append({
                "step": "7_manual_verification",
                "success": False,
                "error": str(e)
            })
    
    return debug_info

@command()
async def mcp_check_tools(context=None):
    """Check availability of installation tools
    
    Example:
    { "mcp_check_tools": {} }
    """
    tools = await MCPServerInstaller.check_tools()
    return tools


@command()
async def mcp_list_dynamic_commands(context=None):
    """List dynamically registered MCP commands
    
    Example:
    { "mcp_list_dynamic_commands": {} }
    """
    commands = mcp_manager.dynamic_commands.get_registered_commands()
    return {"dynamic_commands": commands, "count": len(commands)}


@command()
async def mcp_refresh_dynamic_commands(context=None):
    """Refresh dynamic command registration for all connected servers
    
    Example:
    { "mcp_refresh_dynamic_commands": {} }
    """
    refreshed = []
    for name, session in mcp_manager.sessions.items():
        tools = await session.list_tools()
        await mcp_manager.dynamic_commands.register_tools(name, tools.tools)
        refreshed.append(f"{name}: {len(tools.tools)} tools")
    
    return {"refreshed_servers": refreshed, "total_dynamic_commands": len(mcp_manager.dynamic_commands.get_registered_commands())}
