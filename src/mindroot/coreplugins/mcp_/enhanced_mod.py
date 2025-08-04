import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack

from pydantic import BaseModel
from lib.providers.commands import command
from lib.providers.services import service

from .server_installer import MCPServerInstaller
from .dynamic_commands import MCPDynamicCommands

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


class EnhancedMCPServer(BaseModel):
    """Enhanced MCP server configuration"""
    name: str
    description: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    transport: str = "stdio"
    status: str = "disconnected"
    capabilities: Dict[str, Any] = {}
    
    # Installation config
    install_method: str = "manual"  # uvx, pip, npm, manual
    install_package: Optional[str] = None
    auto_install: bool = False
    installed: bool = False


class EnhancedMCPManager:
    """Enhanced MCP manager with installation and dynamic commands"""
    
    def __init__(self):
        self.servers: Dict[str, EnhancedMCPServer] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stacks: Dict[str, AsyncExitStack] = {}
        self.installer = MCPServerInstaller()
        self.dynamic_commands = MCPDynamicCommands()
        self.config_file = Path("/tmp/mcp_enhanced.json")
        
        # Set sessions reference for dynamic commands
        self.dynamic_commands.set_sessions(self.sessions)
        
        self.load_config()
    
    def load_config(self):
        """Load server configurations"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config in data.items():
                        self.servers[name] = EnhancedMCPServer(**config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save server configurations"""
        try:
            data = {name: server.dict() for name, server in self.servers.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    async def install_server(self, server_name: str) -> bool:
        """Install an MCP server"""
        if server_name not in self.servers:
            return False
        
        server = self.servers[server_name]
        
        if server.install_method == "manual":
            return True
        
        if server.install_method == "uvx":
            success = await self.installer.install_with_uvx(
                server.install_package or server_name
            )
        elif server.install_method == "pip":
            success = await self.installer.install_with_pip(
                server.install_package or server_name
            )
        elif server.install_method == "npm":
            success = await self.installer.install_with_npm(
                server.install_package or server_name
            )
        elif server.install_method == "npx":
            success = await self.installer.install_with_npx(
                server.install_package or server_name
            )
        else:
            return False
        
        if success:
            server.installed = True
            self.save_config()
        
        return success
    
    async def connect_server(self, name: str) -> bool:
        """Connect to an MCP server with enhanced features"""
        if name not in self.servers:
            return False
        
        if ClientSession is None:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        server = self.servers[name]
        
        # Auto-install if needed
        if server.auto_install and not server.installed:
            print(f"Auto-installing {name}...")
            if not await self.install_server(name):
                print(f"Failed to auto-install {name}")
                return False
        
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=server.command,
                args=server.args,
                env=server.env
            )
            
            # Create exit stack
            exit_stack = AsyncExitStack()
            self.exit_stacks[name] = exit_stack
            
            # Connect via stdio
            stdio_transport = await exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            
            # Create session
            session = await exit_stack.enter_async_context(
                ClientSession(stdio_transport[0], stdio_transport[1])
            )
            
            # Initialize
            await session.initialize()
            
            # Store session
            self.sessions[name] = session
            server.status = "connected"
            
            # Get capabilities and register dynamic commands
            try:
                tools = await session.list_tools()
                print(f"DEBUG: Retrieved {len(tools.tools)} tools from {name}")
                for tool in tools.tools:
                    print(f"  Tool: {tool.name} - {tool.description}")
                
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                
                # Safely serialize tools, resources, and prompts
                try:
                    tools_data = []
                    for tool in tools.tools:
                        try:
                            tools_data.append(tool.dict())
                        except Exception as e:
                            print(f"  Warning: Failed to serialize tool {tool.name}: {e}")
                            # Fallback to basic info
                            tools_data.append({
                                "name": tool.name,
                                "description": getattr(tool, 'description', ''),
                                "inputSchema": getattr(tool, 'inputSchema', {})
                            })
                    
                    server.capabilities = {
                        "tools": tools_data,
                        "resources": [res.dict() for res in resources.resources],
                        "prompts": [prompt.dict() for prompt in prompts.prompts]
                    }
                    print(f"DEBUG: Saved {len(tools_data)} tools to server capabilities")
                except Exception as e:
                    print(f"DEBUG: Error serializing capabilities: {e}")
                    # Set basic capabilities even if serialization fails
                    server.capabilities = {
                        "tools": [{"name": t.name, "description": getattr(t, 'description', '')} for t in tools.tools],
                        "resources": [],
                        "prompts": []
                    }
                
                # Register dynamic commands
                print(f"DEBUG: Registering tools for {name}...")
                await self.dynamic_commands.register_tools(name, tools.tools)
                print(f"DEBUG: Successfully registered {len(tools.tools)} tools for {name}")
                
            except Exception as e:
                print(f"Error getting capabilities for {name}: {e}")
            
            self.save_config()
            return True
            
        except Exception as e:
            server.status = "error"
            self.save_config()
            print(f"Error connecting to {name}: {e}")
            return False
    
    async def disconnect_server(self, name: str) -> bool:
        """Disconnect from server and cleanup"""
        if name in self.sessions:
            try:
                # Unregister dynamic commands
                await self.dynamic_commands.unregister_server_tools(name)
                
                # Cleanup session
                if name in self.exit_stacks:
                    await self.exit_stacks[name].aclose()
                    del self.exit_stacks[name]
                
                del self.sessions[name]
                
                if name in self.servers:
                    self.servers[name].status = "disconnected"
                    self.save_config()
                
                return True
            except Exception as e:
                print(f"Error disconnecting {name}: {e}")
                return False
        return True
    
    def add_server(self, name: str, server: EnhancedMCPServer):
        """Add a new server configuration"""
        self.servers[name] = server
        self.save_config()
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            if name in self.sessions:
                asyncio.create_task(self.disconnect_server(name))
            del self.servers[name]
            self.save_config()


# Global enhanced manager
enhanced_mcp_manager = EnhancedMCPManager()


@service()
async def enhanced_mcp_manager_service(params, context=None):
    """Service to access enhanced MCP manager"""
    return enhanced_mcp_manager


@command()
async def mcp_enhanced_connect(server_name: str, context=None):
    """Connect to MCP server with enhanced features
    
    Example:
    { "mcp_enhanced_connect": { "server_name": "calculator" } }
    """
    success = await enhanced_mcp_manager.connect_server(server_name)
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
    success = await enhanced_mcp_manager.disconnect_server(server_name)
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
    server = EnhancedMCPServer(
        name=name,
        description=description or f"MCP server: {name}",
        command="uvx",
        args=[package],
        install_method="uvx",
        install_package=package,
        auto_install=True
    )
    
    enhanced_mcp_manager.add_server(name, server)
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
    server = EnhancedMCPServer(
        name=name,
        description=description or f"MCP server: {name}",
        command="npx",
        args=["-y", package],
        install_method="npx",
        install_package=package,
        auto_install=True
    )
    
    enhanced_mcp_manager.add_server(name, server)
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
        "dynamic_commands": enhanced_mcp_manager.dynamic_commands.get_registered_commands()
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
    if server_name in enhanced_mcp_manager.servers:
        server = enhanced_mcp_manager.servers[server_name]
        server_status = {
            "status": server.status,
            "capabilities": server.capabilities,
            "has_session": server_name in enhanced_mcp_manager.sessions
        }
    
    debug_info["steps"].append({
        "step": "4_server_status",
        "server_found": server_name in enhanced_mcp_manager.servers,
        "server_status": server_status
    })
    
    # Step 5: Check dynamic commands
    final_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    new_commands = [cmd for cmd in final_commands if cmd not in initial_commands]
    
    debug_info["steps"].append({
        "step": "5_dynamic_commands",
        "total_mcp_commands": len(final_commands),
        "new_commands": new_commands,
        "dynamic_commands_tracker": enhanced_mcp_manager.dynamic_commands.get_registered_commands()
    })
    
    # Step 6: Analyze tools
    if server_name in enhanced_mcp_manager.servers:
        server = enhanced_mcp_manager.servers[server_name]
        tools = server.capabilities.get('tools', [])
        tool_analysis = []
        
        for tool in tools:
            tool_name = tool.get('name', 'unknown')
            expected_cmd = f"mcp_{server_name}_{tool_name}"
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
    if server_name in enhanced_mcp_manager.sessions:
        try:
            session = enhanced_mcp_manager.sessions[server_name]
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
    commands = enhanced_mcp_manager.dynamic_commands.get_registered_commands()
    return {"dynamic_commands": commands, "count": len(commands)}


@command()
async def mcp_refresh_dynamic_commands(context=None):
    """Refresh dynamic command registration for all connected servers
    
    Example:
    { "mcp_refresh_dynamic_commands": {} }
    """
    refreshed = []
    for name, session in enhanced_mcp_manager.sessions.items():
        tools = await session.list_tools()
        await enhanced_mcp_manager.dynamic_commands.register_tools(name, tools.tools)
        refreshed.append(f"{name}: {len(tools.tools)} tools")
    
    return {"refreshed_servers": refreshed, "total_dynamic_commands": len(enhanced_mcp_manager.dynamic_commands.get_registered_commands())}
