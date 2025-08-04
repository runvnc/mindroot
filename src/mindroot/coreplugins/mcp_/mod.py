import asyncio
import os
import json
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
from .oauth_storage import MCPTokenStorage

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.streamable_http import streamablehttp_client
    from mcp.client.auth import OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata, OAuthToken, OAuthClientInformationFull
    from pydantic import AnyUrl
    MCP_AVAILABLE = True
except ImportError:
    # MCP not installed yet
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None
    streamablehttp_client = None
    OAuthClientProvider = None
    OAuthClientMetadata = None
    OAuthToken = None
    OAuthClientInformationFull = None
    AnyUrl = None
    MCP_AVAILABLE = False


class MCPServer(BaseModel):
    """Model for MCP server configuration"""
    name: str
    description: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    transport: str = "stdio"  # stdio, sse, websocket, http
    url: Optional[str] = None  # for remote servers
    
    # OAuth 2.0 Configuration
    auth_type: str = "none"  # none, basic, oauth2
    auth_headers: Dict[str, str] = {}  # for basic auth or custom headers
    
    # OAuth 2.0 specific fields
    authorization_server_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None  # For confidential clients
    scopes: List[str] = []
    redirect_uri: Optional[str] = None
    
    # Token storage
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[str] = None  # ISO format datetime string
    
    status: str = "disconnected"  # connected, disconnected, error
    capabilities: Dict[str, Any] = {}


class MCPManager:
    """Manages MCP server connections and operations"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stacks: Dict[str, AsyncExitStack] = {}
        self.pending_oauth_flows: Dict[str, Dict[str, Any]] = {}
        self.config_file = Path("/tmp/mcp_servers.json")
        self.load_config()
    
    def load_config(self):
        """Load server configurations from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    for name, config in data.items():
                        self.servers[name] = MCPServer(**config)
            except Exception as e:
                print(f"Error loading MCP config: {e}")
    
    def save_config(self):
        """Save server configurations to file"""
        try:
            data = {name: server.dict() for name, server in self.servers.items()}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving MCP config: {e}")
            raise e
    
    async def connect_oauth_server(self, name: str) -> bool:
        """Connect to an OAuth-protected MCP server."""
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        
        if server.auth_type != "oauth2":
            return await self.connect_server(name)  # Fallback to regular connection
        
        try:
            # Create OAuth client provider
            # Get BASE_URL from environment, fallback to localhost
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            callback_url = f"{base_url}/mcp_oauth_cb"
            
            oauth_provider = OAuthClientProvider(
                server_url=server.url,
                client_metadata=OAuthClientMetadata(
                    client_name=f"MindRoot MCP Client - {server.name}",
                    redirect_uris=[AnyUrl(server.redirect_uri)] if server.redirect_uri else [AnyUrl(callback_url)],
                    grant_types=["authorization_code", "refresh_token"],
                    response_types=["code"],
                    scope=" ".join(server.scopes) if server.scopes else "user",
                ),
                storage=MCPTokenStorage(name, self),
                redirect_handler=lambda auth_url: self._handle_oauth_redirect(name, auth_url),
                callback_handler=lambda: self._handle_oauth_callback(name),
            )
            
            # Create exit stack for cleanup
            exit_stack = AsyncExitStack()
            self.exit_stacks[name] = exit_stack
            
            # Connect with OAuth using streamable HTTP
            transport = await exit_stack.enter_async_context(
                streamablehttp_client(server.url, auth=oauth_provider)
            )
            
            # Create session
            session = await exit_stack.enter_async_context(
                ClientSession(transport[0], transport[1])
            )
            
            # Initialize the session
            await session.initialize()
            
            # Store session
            self.sessions[name] = session
            
            # Update server status and capabilities
            server.status = "connected"
            
            # Get server capabilities
            try:
                tools = await session.list_tools()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                
                server.capabilities = {
                    "tools": [tool.dict() for tool in tools.tools],
                    "resources": [res.dict() for res in resources.resources],
                    "prompts": [prompt.dict() for prompt in prompts.prompts]
                }
            except Exception as e:
                print(f"Error getting capabilities for {name}: {e}")
            
            self.save_config()
            return True
            
        except Exception as e:
            server.status = "error"
            self.save_config()
            print(f"Error connecting to OAuth server {name}: {e}")
            return False
    
    async def _handle_oauth_redirect(self, server_name: str, auth_url: str) -> None:
        """Handle OAuth redirect - store auth URL for frontend to handle."""
        flow_id = str(uuid.uuid4())
        self.pending_oauth_flows[server_name] = {
            "flow_id": flow_id,
            "auth_url": auth_url,
            "status": "awaiting_authorization",
            "code": None,
            "state": None
        }
        print(f"OAuth flow started for {server_name}: {auth_url}")
    
    async def _handle_oauth_callback(self, server_name: str) -> tuple[str, Optional[str]]:
        """Handle OAuth callback - get code from pending flow."""
        if server_name not in self.pending_oauth_flows:
            raise ValueError(f"No pending OAuth flow for server {server_name}")
        
        flow = self.pending_oauth_flows[server_name]
        
        # Wait for callback to be processed by frontend
        max_wait = 300  # 5 minutes
        wait_time = 0
        
        while flow["status"] == "awaiting_authorization" and wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
        
        if flow["status"] != "callback_received":
            raise ValueError("OAuth authorization timed out or failed")
        
        code = flow["code"]
        state = flow["state"]
        
        # Clean up flow
        del self.pending_oauth_flows[server_name]
        
        return code, state
    
    def start_oauth_flow(self, server_name: str) -> Optional[str]:
        """Start OAuth flow and return authorization URL."""
        if server_name in self.pending_oauth_flows:
            flow = self.pending_oauth_flows[server_name]
            if flow["status"] == "awaiting_authorization":
                return flow["auth_url"]
        return None
    
    def complete_oauth_flow(self, server_name: str, code: str, state: Optional[str] = None) -> bool:
        """Complete OAuth flow with authorization code."""
        if server_name not in self.pending_oauth_flows:
            return False
        
        flow = self.pending_oauth_flows[server_name]
        flow["code"] = code
        flow["state"] = state
        flow["status"] = "callback_received"
        
        return True
    
    def get_oauth_status(self, server_name: str) -> Dict[str, Any]:
        """Get OAuth flow status for a server."""
        if server_name not in self.servers:
            return {"error": "Server not found"}
        
        server = self.servers[server_name]
        
        status = {
            "server_name": server_name,
            "auth_type": server.auth_type,
            "status": server.status,
            "has_tokens": bool(server.access_token),
            "token_expires_at": server.token_expires_at,
            "scopes": server.scopes
        }
        
        if server_name in self.pending_oauth_flows:
            flow = self.pending_oauth_flows[server_name]
            status["oauth_flow"] = {
                "flow_id": flow["flow_id"],
                "status": flow["status"],
                "auth_url": flow["auth_url"] if flow["status"] == "awaiting_authorization" else None
            }
        
        return status
    
    async def connect_remote_server(self, name: str) -> bool:
        """Connect to a remote MCP server (HTTP/SSE)."""
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        
        if server.auth_type == "oauth2":
            return await self.connect_oauth_server(name)
        
        # Handle basic auth or no auth remote servers
        try:
            # Create exit stack for cleanup
            exit_stack = AsyncExitStack()
            self.exit_stacks[name] = exit_stack
            
            # Connect via streamable HTTP
            transport = await exit_stack.enter_async_context(
                streamablehttp_client(server.url)
            )
            
            # Create session
            session = await exit_stack.enter_async_context(
                ClientSession(transport[0], transport[1])
            )
            
            # Initialize the session
            await session.initialize()
            
            # Store session
            self.sessions[name] = session
            
            # Update server status and capabilities
            server.status = "connected"
            
            # Get server capabilities
            try:
                tools = await session.list_tools()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                
                server.capabilities = {
                    "tools": [tool.dict() for tool in tools.tools],
                    "resources": [res.dict() for res in resources.resources],
                    "prompts": [prompt.dict() for prompt in prompts.prompts]
                }
            except Exception as e:
                print(f"Error getting capabilities for {name}: {e}")
            
            self.save_config()
            return True
            
        except Exception as e:
            server.status = "error"
            self.save_config()
            print(f"Error connecting to remote server {name}: {e}")
            return False
    
    async def connect_server(self, name: str) -> bool:
        """Connect to an MCP server"""
        if name not in self.servers:
            return False
        
        if ClientSession is None:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        server = self.servers[name]
        
        # Route to appropriate connection method based on transport
        if server.transport in ["http", "sse", "websocket"] or server.url:
            return await self.connect_remote_server(name)
        
        try:
            if server.transport == "stdio":
                # Create server parameters
                server_params = StdioServerParameters(
                    command=server.command,
                    args=server.args,
                    env=server.env
                )
                
                # Create exit stack for cleanup
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
                
                # Initialize the session
                await session.initialize()
                
                # Store session
                self.sessions[name] = session
                
                # Update server status and capabilities
                server.status = "connected"
                
                # Get server capabilities
                try:
                    tools = await session.list_tools()
                    resources = await session.list_resources()
                    prompts = await session.list_prompts()
                    
                    server.capabilities = {
                        "tools": [tool.dict() for tool in tools.tools],
                        "resources": [res.dict() for res in resources.resources],
                        "prompts": [prompt.dict() for prompt in prompts.prompts]
                    }
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
        """Disconnect from an MCP server"""
        if name in self.sessions:
            try:
                # Clean up exit stack (this will close the session)
                if name in self.exit_stacks:
                    await self.exit_stacks[name].aclose()
                    del self.exit_stacks[name]
                
                del self.sessions[name]
                
                if name in self.servers:
                    self.servers[name].status = "disconnected"
                    self.save_config()
                
                return True
            except Exception as e:
                print(f"Error disconnecting from {name}: {e}")
                return False
        return True
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an MCP server"""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        session = self.sessions[server_name]
        result = await session.call_tool(tool_name, arguments)
        return result
    
    async def read_resource(self, server_name: str, uri: str) -> Any:
        """Read a resource from an MCP server"""
        if server_name not in self.sessions:
            raise ValueError(f"Server {server_name} not connected")
        
        session = self.sessions[server_name]
        result = await session.read_resource(uri)
        return result
    
    def add_server(self, name: str, server: MCPServer):
        """Add a new server configuration"""
        self.servers[name] = server
        self.save_config()
    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            # Disconnect first if connected
            if name in self.sessions:
                asyncio.create_task(self.disconnect_server(name))
            
            del self.servers[name]
            self.save_config()


# Global MCP manager instance
mcp_manager = MCPManager()


@service()
async def mcp_manager_service(context=None):
    """Service to access the MCP manager"""
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
