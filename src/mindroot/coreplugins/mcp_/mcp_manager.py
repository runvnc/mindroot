import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack
from urllib.parse import parse_qs, urlparse

import httpx
from pydantic import BaseModel

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
    TokenStorage = None
    MCP_AVAILABLE = False


class InMemoryTokenStorage:
    """Demo In-memory token storage implementation."""

    def __init__(self):
        self.tokens: Optional[Any] = None
        self.client_info: Optional[Any] = None

    async def get_tokens(self):
        """Get stored tokens."""
        return self.tokens

    async def set_tokens(self, tokens):
        """Store tokens."""
        self.tokens = tokens

    async def get_client_info(self):
        """Get stored client information."""
        return self.client_info

    async def set_client_info(self, client_info):
        """Store client information."""
        self.client_info = client_info


class MCPServer(BaseModel):
    """Model for MCP server configuration"""
    name: str
    description: str
    command: str
    args: List[str] = []
    env: Dict[str, str] = {}
    transport: str = "stdio"  # stdio, sse, websocket, http
    url: Optional[str] = None  # for remote servers (legacy single URL)
    # New: explicit provider vs transport URLs
    provider_url: Optional[str] = None  # e.g., https://mcp.notion.com
    transport_url: Optional[str] = None  # e.g., https://mcp.notion.com/sse or /mcp
    transport_type: Optional[str] = None  # "sse" | "streamable_http"
    
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
    
    # Installation config (Enhanced features)
    install_method: str = "manual"  # uvx, pip, npm, manual
    install_package: Optional[str] = None
    auto_install: bool = False
    installed: bool = False


class MCPManager:
    """Manages MCP server connections and operations"""
    
    def __init__(self):
        self.servers: Dict[str, MCPServer] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stacks: Dict[str, AsyncExitStack] = {}
        self.background_tasks: Dict[str, asyncio.Task] = {}
        self.pending_oauth_flows: Dict[str, Dict[str, Any]] = {}
        self.installer = MCPServerInstaller()
        self.dynamic_commands = MCPDynamicCommands()
        self.config_file = Path("/tmp/mcp_servers.json")
        
        # Set sessions reference for dynamic commands
        self.dynamic_commands.set_sessions(self.sessions)
        
        self.load_config()

    # ---- URL/Transport helpers ----
    def _infer_urls(self, server: MCPServer) -> tuple[str, str, str]:
        """Infer provider_url, transport_url, and transport_type from server fields.

        transport_type returns one of: 'sse', 'streamable_http'.
        """
        # Prefer explicit transport_url, otherwise fallback to legacy url
        turl = (server.transport_url or server.url or "").strip()
        if not turl:
            # As last resort, try to build from provider_url + transport
            if server.provider_url and server.transport:
                base = server.provider_url.rstrip('/')
                if server.transport == 'sse':
                    turl = f"{base}/sse"
                elif server.transport in ('http', 'streamable_http'):
                    turl = f"{base}/mcp"
        # Determine type from suffix if not set
        ttype = server.transport_type
        if not ttype:
            if turl.endswith('/sse'):
                ttype = 'sse'
            elif turl.endswith('/mcp'):
                ttype = 'streamable_http'
            else:
                # fallback based on declared transport
                if server.transport == 'sse':
                    ttype = 'sse'
                else:
                    ttype = 'streamable_http'
        # Determine provider_url
        provider = server.provider_url
        if not provider:
            # Strip known suffixes
            if turl.endswith('/sse'):
                provider = turl[: -len('/sse')]
            elif turl.endswith('/mcp'):
                provider = turl[: -len('/mcp')]
            else:
                # Use scheme://host[:port]
                try:
                    from urllib.parse import urlsplit
                    parts = urlsplit(turl)
                    if parts.scheme and parts.netloc:
                        provider = f"{parts.scheme}://{parts.netloc}"
                    else:
                        provider = turl.rstrip('/')
                except Exception:
                    provider = turl.rstrip('/')
        return provider.rstrip('/'), turl.rstrip('/'), ttype

    def _update_server_urls(self, name: str, provider_url: str, transport_url: str, transport_type: str) -> None:
        """Persist inferred URL fields back to the server config if missing/outdated."""
        srv = self.servers.get(name)
        if not srv:
            return
        changed = False
        if not srv.provider_url:
            srv.provider_url = provider_url
            changed = True
        if not srv.transport_url:
            srv.transport_url = transport_url
            changed = True
        if not srv.transport_type:
            srv.transport_type = transport_type
            changed = True
        if changed:
            self.save_config()

    def _build_oauth_provider(self, name: str, server: MCPServer, provider_url: str):
        """Create an OAuthClientProvider bound to this server using persistent storage."""
        base_url = os.getenv('BASE_URL', 'http://localhost:3000')
        callback_url = f"{base_url.rstrip('/')}/mcp_oauth_cb"
        # Storage persists tokens into the server record
        storage = MCPTokenStorage(name, self)
        metadata = OAuthClientMetadata(
            client_name=f"MindRoot - {server.name}",
            redirect_uris=[AnyUrl(callback_url)] if AnyUrl else [callback_url],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope=" ".join(server.scopes) if server.scopes else "user",
        )
        print("DEBUG: -------------------------------------------------------")
        print("DEBUG: OAuth provider server_url:", provider_url)
        oauth_provider = OAuthClientProvider(
            server_url=provider_url,
            client_metadata=metadata,
            storage=storage,
            redirect_handler=lambda auth_url: self._handle_oauth_redirect(name, auth_url),
            callback_handler=lambda: self._handle_oauth_callback(name),
        )
        return oauth_provider
    
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

    async def _persistent_oauth_connection(self, name: str) -> None:
        """Background task to maintain persistent OAuth connection."""
        server = self.servers[name]
        print(f"DEBUG: Starting persistent OAuth connection task for {name}")
        
        try:
            # Create OAuth client provider
            base_url = os.getenv('BASE_URL', 'http://localhost:3000')
            callback_url = f"{base_url.rstrip('/')}/mcp_oauth_cb"
            
            oauth_provider = OAuthClientProvider(
                server_url=server.url,
                client_metadata=OAuthClientMetadata(
                    client_name="test",
                    redirect_uris=[AnyUrl(callback_url)],
                    grant_types=["authorization_code", "refresh_token"],
                    response_types=["code"],
                    scope="user"
                ),
                storage=InMemoryTokenStorage(),
                redirect_handler=lambda auth_url: self._handle_oauth_redirect(name, auth_url),
                callback_handler=lambda: self._handle_oauth_callback(name)
            )
            
            print(f"DEBUG: Persistent task connecting to {server.url}")
            
            # Keep connection alive indefinitely
            async with streamablehttp_client(server.url, auth=oauth_provider) as (read, write, _):
                print(f"DEBUG: Persistent transport created for {name}")
                async with ClientSession(read, write) as session:
                    print(f"DEBUG: Persistent session created for {name}")
                    
                    # Initialize the session
                    await session.initialize()
                    print(f"DEBUG: Persistent session initialized for {name}")
                    
                    # Store session globally
                    self.sessions[name] = session
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
                        print(f"DEBUG: Retrieved capabilities for {name}: {len(tools.tools)} tools")
                    except Exception as e:
                        print(f"Error getting capabilities for {name}: {e}")
                    
                    self.save_config()
                    print(f"DEBUG: Persistent connection established for {name}")
                    
                    # Keep the task alive until cancelled
                    try:
                        while True:
                            await asyncio.sleep(60)  # Heartbeat every minute
                    except asyncio.CancelledError:
                        print(f"DEBUG: Persistent connection task cancelled for {name}")
                        raise
                        
        except Exception as e:
            print(f"ERROR: Persistent OAuth connection failed for {name}: {e}")
            server.status = "error"
            self.save_config()
            raise

    async def connect_oauth_server(self, name: str) -> bool:
        """Connect to an OAuth-protected MCP server."""
        print("Connecting to OAuth server:", name)
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        print('1')
        if name not in self.servers:
            print("Server not found:", name)
            return False
        
        server = self.servers[name]
        print('2')
        if server.auth_type != "oauth2":
            print("Server is not configured for OAuth2:", name)
            return await self.connect_server(name)  # Fallback to regular connection
        
        print(f"DEBUG: Starting OAuth connection for {name}")
        
        # If already connected via background task, return success
        if name in self.background_tasks and not self.background_tasks[name].done():
            print(f"DEBUG: OAuth server {name} already connected via background task")
            return True
        
        # Clean up any old background task
        if name in self.background_tasks:
            self.background_tasks[name].cancel()
            del self.background_tasks[name]
        
        try:
            # Start background task for persistent connection
            task = asyncio.create_task(self._persistent_oauth_connection(name))
            self.background_tasks[name] = task
            
            # Wait longer for OAuth flow to potentially start
            await asyncio.sleep(5)
            
            # Check if connection was successful or OAuth flow started
            if name in self.sessions and server.status == "connected":
                print(f"DEBUG: Background OAuth connection successful for {name}")
                return True
            elif name in self.pending_oauth_flows:
                print(f"DEBUG: OAuth flow started for {name}, frontend should handle popup")
                return False  # This will trigger the OAuth flow check in the calling code
            else:
                print(f"DEBUG: Background OAuth connection failed for {name}")
                return False
                
        except Exception as e:
            server.status = "error"
            self.save_config()
            print(f"Error starting OAuth connection for {name}: {e}")
            return False
    
    async def _handle_oauth_redirect(self, server_name: str, auth_url: str) -> None:
        """Handle OAuth redirect - store auth URL for frontend to handle."""
        flow_id = str(uuid.uuid4())
        print(f"DEBUG: Creating OAuth flow for {server_name}")
        print(f"DEBUG: Auth URL: {auth_url}")
        self.pending_oauth_flows[server_name] = {
            "flow_id": flow_id,
            "auth_url": auth_url,
            "status": "awaiting_authorization",
            "code": None,
            "state": None
        }
        print(f"DEBUG: OAuth flow created with ID: {flow_id}")
        print(f"OAuth flow started for {server_name}: {auth_url}")
    
    async def _handle_oauth_callback(self, server_name: str) -> tuple[str, Optional[str]]:
        """Handle OAuth callback - get code from pending flow."""
        if server_name not in self.pending_oauth_flows:
            print(f"DEBUG: No pending OAuth flow found for {server_name}")
            print(f"DEBUG: Available flows: {list(self.pending_oauth_flows.keys())}")
            raise ValueError(f"No pending OAuth flow for server {server_name}")
        
        flow = self.pending_oauth_flows[server_name]
        
        # Wait for callback to be processed by frontend
        max_wait = 300  # 5 minutes
        wait_time = 0
        print(f"DEBUG: Waiting for OAuth callback for {server_name}, current status: {flow['status']}")
        
        while flow["status"] == "awaiting_authorization" and wait_time < max_wait:
            if wait_time % 10 == 0:  # Log every 10 seconds
                print(f"DEBUG: Still waiting for OAuth callback... {wait_time}s elapsed")
            await asyncio.sleep(1)
            wait_time += 1
        
        print(f"DEBUG: OAuth wait completed. Status: {flow['status']}, wait_time: {wait_time}")
        code = flow["code"]
        state = flow["state"]
 
        print(f"DEBUG: OAuth flow completed for {server_name}, code: {code}, state: {state}")
 
        if flow["status"] != "callback_received":
            raise ValueError("OAuth authorization timed out or failed")
        
        # Clean up flow
        del self.pending_oauth_flows[server_name]
        
        return code, state

    def start_oauth_flow(self, server_name: str) -> Optional[str]:
        """Start OAuth flow and return authorization URL."""
        if server_name in self.pending_oauth_flows:
            print(f"DEBUG: Found existing OAuth flow for {server_name}")
            flow = self.pending_oauth_flows[server_name]
            if flow["status"] == "awaiting_authorization":
                print(f"DEBUG: Returning existing auth URL: {flow['auth_url']}")
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
        print("remote connect")
        if not MCP_AVAILABLE:
            print("import error")
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        if name not in self.servers:
            print("Server not found:", name)
            return False
        
        server = self.servers[name]
        
        if server.auth_type == "oauth2":
            print("connect oauth server:", name)
            return await self.connect_oauth_server(name)
        
        # Handle basic auth or no auth remote servers
        try:
            # Create exit stack for cleanup
            exit_stack = AsyncExitStack()
            self.exit_stacks[name] = exit_stack
            
            # Determine transport details
            provider_url, transport_url, transport_type = self._infer_urls(server)
            self._update_server_urls(name, provider_url, transport_url, transport_type)
            
            # Use appropriate transport based on type
            if transport_type == "sse":
                print(f"Connecting via SSE to: {transport_url}")
                transport = await exit_stack.enter_async_context(
                    sse_client(transport_url)
                )
                # SSE returns (read, write) - no session_id
                session = await exit_stack.enter_async_context(
                    ClientSession(transport[0], transport[1])
                )
            else:  # streamable_http
                print(f"Connecting via StreamableHTTP to: {transport_url}")
                transport = await exit_stack.enter_async_context(
                    streamablehttp_client(transport_url)
                )
                # StreamableHTTP returns (read, write, get_session_id)
                session = await exit_stack.enter_async_context(
                    ClientSession(transport[0], transport[1])
                )
            print("Session created:", session)
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

    async def sanity_test(self) -> str:
        print("Basic MCP Manager sanity test")
        return "OK"

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
        """Connect to an MCP server"""
        print("Connecting to MCP server:", name)
        if name not in self.servers:
            print("Server not found:", name)
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
        """Disconnect from an MCP server"""
        if name in self.sessions:
            try:
                # Unregister dynamic commands
                await self.dynamic_commands.unregister_server_tools(name)
                
                # Cancel background task if it exists
                if name in self.background_tasks:
                    print(f"DEBUG: Cancelling background task for {name}")
                    self.background_tasks[name].cancel()
                    try:
                        await self.background_tasks[name]
                    except asyncio.CancelledError:
                        pass
                    del self.background_tasks[name]
                
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
