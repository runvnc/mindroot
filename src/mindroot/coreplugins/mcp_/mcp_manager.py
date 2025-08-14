import asyncio
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import AsyncExitStack
import re
from urllib.parse import parse_qs, urlparse
import traceback

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
    from mcp.client.auth import OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata
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

def _substitute_secrets(config_item: Any, secrets: Dict[str, str]) -> Any:
    if not secrets or config_item is None:
        print("DEBUG: No secrets to substitute or config_item is None, not substituting", config_item)
        return config_item

    if isinstance(config_item, str):
        print("String")
        # Find all placeholders like <SECRET_NAME> or ${SECRET_NAME}
        # This regex captures the name inside the brackets/braces
        placeholder_keys = re.findall(r'<([A-Z0-9_]+)>|\${([A-Z0-9_]+)}', config_item)
        # Flatten list of tuples and remove empty matches
        keys_to_replace = [key for tpl in placeholder_keys for key in tpl if key]

        temp_item = config_item
        for key in keys_to_replace:
            if key in secrets:
                # Replace both placeholder formats
                temp_item = temp_item.replace(f'<{key}>', secrets[key])
                temp_item = temp_item.replace(f'${{{key}}}', secrets[key])
        return temp_item

    if isinstance(config_item, list):
        print("List")
        return [_substitute_secrets(item, secrets) for item in config_item]

    if isinstance(config_item, dict):
        print("DEBUG: Substituting secrets in config_item (dict)")
        return {k: _substitute_secrets(v, secrets) for k, v in config_item.items()}

    return config_item



class MCPServer(BaseModel):
    """Model for MCP server configuration"""
    name: str
    description: str
    command: Optional[str] = None
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
    secrets: Optional[Dict[str, str]] = None
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
        # Debug/diagnostics: short-lived cache of last discovered capabilities per server
        self.last_capabilities: Dict[str, Dict[str, Any]] = {}
        self.installer = MCPServerInstaller()
        self.dynamic_commands = MCPDynamicCommands()
        self.config_file = Path("/tmp/mcp_servers.json")
        
        # Set sessions reference for dynamic commands
        self.dynamic_commands.set_sessions(self.sessions)
        
        self.load_config()

    # ---- Serialization helpers ----
    def _server_to_jsonable(self, server: MCPServer) -> Dict[str, Any]:
        """Convert server model to plain JSON-serializable dict.
        Ensures AnyUrl or other exotic types are stringified.
        """
        # Start with pydantic dict (already basic types), but normalize URLs just in case
        data = server.dict()
        for key in ("url", "provider_url", "transport_url", "authorization_server_url", "redirect_uri"):
            val = data.get(key)
            if val is not None and not isinstance(val, (str, int, float, bool)):  # e.g., AnyUrl
                try:
                    data[key] = str(val)
                except Exception:
                    data[key] = f"{val}"
        return data

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
        #if changed:
            #self.save_config()
        # Debug log
        try:
            print(f"DEBUG: _update_server_urls: name={name} provider={provider_url} transport={transport_url} type={transport_type}")
        except Exception:
            pass

    def _build_oauth_provider(self, name: str, server: MCPServer, provider_url: str):
        """Create an OAuthClientProvider bound to this server using persistent storage."""
        base_url = os.getenv('BASE_URL', 'http://localhost:3000')
        callback_url = f"{base_url.rstrip('/')}/mcp_oauth_cb"
        # Storage persists tokens into the server record
        storage = MCPTokenStorage(name, self)
        metadata = OAuthClientMetadata(
            client_name=f"MindRoot - {server.name}",
            # Use plain string to avoid pydantic AnyUrl leaking into persisted state
            redirect_uris=[str(callback_url)],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
            scope=" ".join(server.scopes) if server.scopes else "user",
        )
        print("DEBUG: -------------------------------------------------------")
        print("DEBUG: OAuth provider server_url:", provider_url)

        print("DEBUG: OAuth provider metadata:", metadata.dict())
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
        """Save server configurations to file - LOCAL SERVERS ONLY"""
        try:
            data = {}
            for name, server in self.servers.items():
                # Only save local servers (stdio transport with no URL)
                print("Determining if server is local:", name, server.transport, server.url, server.provider_url, server.transport_url, server.command)
                if self._is_local_server(server):
                    print(f"DEBUG: Saving local server {name} to config")
                    data[name] = self._server_to_jsonable(server)
                else:
                    print(f"DEBUG: Skipping remote server {name} from config")

            print(f"DEBUG: Saving {len(data)} local servers to config (filtered out {len(self.servers) - len(data)} remote servers)")
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving MCP config: {e}")
            raise e
    
    def _is_local_server(self, server: MCPServer) -> bool:
        """Determine if a server is local (should be persisted) or remote (session-only)"""
        # Local servers use stdio transport and have no URL
        return (server.transport == "stdio" and 
                not server.url and 
                not server.provider_url and 
                not server.transport_url and
                server.command)  # Local servers must have a command
    
    def mark_server_as_installed(self, name: str, registry_id: str = None):
        """Mark server as installed (in-memory only for remote servers)"""
        if name in self.servers:
            self.servers[name].installed = True
            if registry_id:
                setattr(self.servers[name], 'registry_id', registry_id)
            
            # Only save to config if it's a local server
            if self._is_local_server(self.servers[name]):
                self.save_config()
    async def _persistent_oauth_connection(self, name: str) -> None:
        """Background task to maintain persistent OAuth connection."""
        server = self.servers[name]
        print(f"DEBUG: Starting persistent OAuth connection task for {name}")
        
        try:
            # Determine transport details and ensure config is updated
            provider_url, transport_url, transport_type = self._infer_urls(server)
            self._update_server_urls(name, provider_url, transport_url, transport_type)

            # Create OAuth client provider using persistent storage
            oauth_provider = self._build_oauth_provider(name, server, provider_url)

            print(f"DEBUG: Persistent task connecting to {transport_url} via {transport_type}")

            # Keep connection alive indefinitely using appropriate transport
            if transport_type == "sse":
                print(f"DEBUG: About to create SSE client for {transport_url}")
                print(f"DEBUG: OAuth provider: {oauth_provider}")
                async with sse_client(url=transport_url, auth=oauth_provider) as (read, write):
                    print(f"DEBUG: Persistent SSE transport created for {name}")
                    print(f"DEBUG: SSE read: {read}, write: {write}")
                    print(f"DEBUG: About to create ClientSession")
                    async with ClientSession(read, write) as session:
                        print(f"DEBUG: Persistent session created for {name}")
                        
                        # Initialize the session
                        print(f"DEBUG: About to initialize session for {name}")
                        await session.initialize()
                        print(f"DEBUG: Persistent session initialized for {name}")
                        
                        # Store session globally
                        self.sessions[name] = session
                        server.status = "connected"
                        
                        # Get server capabilities
                        try:
                            tools = []
                            resources = []
                            prompts = []
                            print(f"DEBUG: About to list tools for {name}")
                            print("DEBUG: listing tools")
                            tools = await session.list_tools()
                            print("DEBUG: tools listed successfully", tools)
                            print("DEBUG: listing resources")
                            try:
                                resources = await session.list_resources()
                            except Exception as e:
                                print(f"Error listing resources for {name}: {e}")
                                resources = []
                            print("DEBUG: resources listed successfully", resources)
                            print("DEBUG: listing prompts")
                            try:
                                prompts = await session.list_prompts()
                            except Exception as e:
                                print(f"Error listing prompts for {name}: {e}")

                            print(f"DEBUG: Processing capabilities - tools type: {type(tools)}, tools: {tools}")
                            server.capabilities = {
                                "tools": [tool.dict() for tool in tools.tools]
                                #"resources": [res.dict() for res in resources.resources]
                            }
                            self.servers[name] = server
                            self.last_capabilities[name] = server.capabilities
                            print(f"DEBUG: Retrieved capabilities for {name}: {len(tools.tools)} tools")
                            
                            # Register dynamic commands
                            print(f"DEBUG: Registering tools for {name}...")
                            await self.dynamic_commands.register_tools(name, tools.tools)
                            print(f"DEBUG: Successfully registered {len(tools.tools)} tools for {name}")
                        except Exception as e:
                            print(f"Error getting capabilities for {name}: {e}")
                            # Don't set status to error if we got this far - keep it connected
                            pass
                        
                        #self.save_config()
                        print(f"DEBUG: Capabilities saved for {name}, tools={len(server.capabilities.get('tools', []))}")
                        print(f"DEBUG: Persistent SSE connection established for {name}")

                        # Keep the task alive until cancelled
                        try:
                            while True:
                                await asyncio.sleep(60)  # Heartbeat every minute
                        except asyncio.CancelledError:
                            print(f"DEBUG: Persistent connection task cancelled for {name}")
                            raise
            else:
                async with streamablehttp_client(url=transport_url, auth=oauth_provider) as (read, write, _):
                    print(f"DEBUG: Persistent StreamableHTTP transport created for {name}")
                    async with ClientSession(read, write) as session:
                        print(f"DEBUG: Persistent session created for {name}")
                        
                        # Initialize the session
                        print(f"DEBUG: About to initialize session for {name}")
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
                            self.last_capabilities[name] = server.capabilities
                            # Save to diagnostics cache
                            self.last_capabilities[name] = server.capabilities
                            print(f"DEBUG: Retrieved capabilities for {name}: {len(tools.tools)} tools")
                            
                            # Register dynamic commands
                            print(f"DEBUG: Registering tools for {name}...")
                            await self.dynamic_commands.register_tools(name, tools.tools)
                            print(f"DEBUG: Successfully registered {len(tools.tools)} tools for {name}")
                        except Exception as e:
                            print(f"Error getting capabilities for {name}: {e}")
                            # Don't set status to error if we got this far - keep it connected
                            pass
                        
                        #self.save_config()
                        print(f"DEBUG: Capabilities saved for {name}, tools={len(server.capabilities.get('tools', []))}")
                        print(f"DEBUG: Capabilities saved for {name}, tools={len(server.capabilities.get('tools', []))}")
                        print(f"DEBUG: Persistent StreamableHTTP connection established for {name}")
                        
                        # Keep the task alive until cancelled
                        try:
                            while True:
                                await asyncio.sleep(60)  # Heartbeat every minute
                        except asyncio.CancelledError:
                            print(f"DEBUG: Persistent connection task cancelled for {name}")
                            raise
                        
        except Exception as e:
            print(f"ERROR: Persistent OAuth connection failed for {name}: {e}")
            import traceback
            traceback.print_exc()
            t = traceback.format_exc()
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
            print("Server not found:", name, " Known:", list(self.servers.keys()))
            return False
        
        server = self.servers[name]
        print('2')
        if server.auth_type != "oauth2":
            print("Server is not configured for OAuth2:", name)
            return await self.connect_server(name)  # Fallback to regular connection
        
        print(f"DEBUG: Starting OAuth connection for {name}")
       

        # If already connected via background task, return success
        if False and name in self.background_tasks and not self.background_tasks[name].done():
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
            await asyncio.sleep(2)
            
            # Check if connection was successful or OAuth flow started
            if name in self.sessions and server.status == "connected":
                print(f"DEBUG: Background OAuth connection successful for {name}")
                return True
            elif False and server.status == "error":
                print(f"DEBUG: Background OAuth connection failed for {name}")
                # Check if the background task had an exception
                if not task.done():
                    task.cancel()
                return False
            elif name in self.pending_oauth_flows:
                print(f"DEBUG: OAuth flow started for {name}, frontend should handle popup")
                return False  # This will trigger the OAuth flow check in the calling code
            else:
                print(f"DEBUG: (X) Background OAuth connection failed for {name}, {server.status} {self.sessions}")
                return False
                
        except Exception as e:
            server.status = "error"
            t = traceback.format_exc()
            self.save_config()
            print(f"Error starting OAuth connection for {name}: {e}\n{t}")
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
            print(f"DEBUG: complete_oauth_flow: server_name '{server_name}' not in pending flows. Available: {list(self.pending_oauth_flows.keys())}")
            return False
        
        flow = self.pending_oauth_flows[server_name]
        flow["code"] = code
        flow["state"] = state
        flow["status"] = "callback_received"
        print(f"DEBUG: complete_oauth_flow: marked callback_received for {server_name}, state={state} code_present={bool(code)}")
        
        return True
    
    def get_oauth_status(self, server_name: str) -> Dict[str, Any]:
        """Get OAuth flow status for a server."""
        if server_name not in self.servers:
            print(f"DEBUG: get_oauth_status: Server not found: '{server_name}'. Known servers: {list(self.servers.keys())}")
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
        # Add diagnostics: last capabilities snapshot size
        try:
            if server_name in self.last_capabilities:
                status["last_tools_count"] = len(self.last_capabilities[server_name].get("tools", []))
        except Exception:
            pass
        
        return status
    
    async def connect_remote_server(self, name: str) -> bool:
        """Connect to a remote MCP server (HTTP/SSE)."""
        print("remote connect")
        if not MCP_AVAILABLE:
            print("import error")
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        if name not in self.servers:
            print("Server not found:", name, " Known:", list(self.servers.keys()))
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
                self.last_capabilities[name] = server.capabilities
            except Exception as e:
                print(f"Error getting capabilities for {name}: {e}")
            
            self.save_config()
            print(f"DEBUG: connect_remote_server: saved capabilities for {name}, tools={len(server.capabilities.get('tools', []))}")
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
            # Only save config for local servers
            if self._is_local_server(server):
                self.save_config()
        
        return success

    async def connect_server(self, name: str, secrets: Optional[Dict[str, str]] = None) -> bool:
        """Connect to an MCP server"""
        print("Connecting to MCP server:", name)
        if name not in self.servers:
            print("Server not found:", name, " Known:", list(self.servers.keys()))
            return False
        if ClientSession is None:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        server = self.servers[name]
        print("DEBUG: secrets passed in connect_server:", secrets) 
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
                import copy

                # Combine stored secrets with any provided for this session
                all_secrets = (server.secrets or {}).copy()
                if secrets:
                    for k, v in secrets.items():
                        if v is not None and v != "":
                            all_secrets[k] = v

                final_command = _substitute_secrets(server.command, all_secrets)
                args_ = _substitute_secrets(copy.deepcopy(server.args), all_secrets)
                env_ = _substitute_secrets(copy.deepcopy(server.env), all_secrets)
                for key, value in all_secrets.items():
                    if key in env_:
                        if value is not None and value is not "":
                            env_[key] = value
                final_env = {k: v for k, v in env_.items() if v is not None}
                final_args = [str(arg) for arg in args_ if arg is not None]
                print("DEBUG: server secrets:", server.secrets)
                print(f"DEBUG: connect_server: final_command={final_command}, final_args={final_args}, final_env={final_env}")
                # Create server parameters
                server_params = StdioServerParameters(
                    command=final_command,
                    args=final_args,
                    env=final_env
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
                    
                    #resources = await session.list_resources()
                    #prompts = await session.list_prompts()
                    
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
                            "tools": tools_data #,
                            #"resources": [res.dict() for res in resources.resources],
                            #"prompts": [prompt.dict() for prompt in prompts.prompts]
                        }
                        self.servers[name] = server
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
                
                # Only save config for local servers
                if self._is_local_server(server):
                    self.save_config()
                
                return True
                
        except Exception as e:
            print("DEBUG: Error connecting to MCP server:", name, e)
            import traceback
            traceback.print_exc()
            server.status = "error"
            self.save_config()
            print(f"Error connecting to {name}: {e}")
            return False

    async def test_local_server_capabilities(self, name: str, command: str, args: List[str], env: Dict[str, str], secrets: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Test connection to a local MCP server and return its capabilities.
        
        This method creates a temporary server, connects to it, extracts capabilities,
        and cleans up. It follows the same pattern as the working catalog system.
        
        Args:
            name: Display name for the server (for error messages)
            command: Command to run the MCP server
            args: Arguments for the command
            env: Environment variables
            secrets: A dictionary of secrets to substitute into placeholders.
            
        Returns:
            Dict containing success status, message, and capabilities (tools, resources, prompts)
            
        Raises:
            Exception: If MCP SDK is not available or connection fails
        """
        if not MCP_AVAILABLE:
            raise ImportError("MCP SDK not installed. Run: pip install mcp")
        
        if not command:
            raise ValueError("Command is required for local servers")
        
        # Generate unique temporary server name
        temp_server_name = f"temp_local_test_{uuid.uuid4().hex[:8]}"
        
        try:
            # Create temporary server configuration (following catalog pattern)
            temp_server = MCPServer(
                name=temp_server_name,
                description=f"Temporary local server for testing {name}",
                command=command,
                args=args,
                env=env,
                transport="stdio",  # Explicitly set stdio transport
                # Explicitly do NOT set url field for local servers
            )
            
            print(f"DEBUG: test_local_server_capabilities: Created temp server {temp_server_name}")
            
            # Add temporary server to MCP manager
            self.add_server(temp_server_name, temp_server)
            
            # Connect to server (this will use stdio connection)
            success = await self.connect_server(temp_server_name, secrets=secrets)
            if not success:
                raise Exception("Failed to connect to local server")
            
            print(f"DEBUG: test_local_server_capabilities: Connected to {temp_server_name}")
            
            # Get server capabilities
            server = self.servers[temp_server_name]
            tools = server.capabilities.get("tools", [])
            resources = server.capabilities.get("resources", [])
            prompts = server.capabilities.get("prompts", [])
            
            print(f"DEBUG: test_local_server_capabilities: Found {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts")
            
            return {
                "success": True,
                "message": f"Successfully connected to local server. Found {len(tools)} tools, {len(resources)} resources, {len(prompts)} prompts.",
                "tools": tools,
                "resources": resources,
                "prompts": prompts
            }
            
        finally:
            # Clean up temporary server
            try:
                if temp_server_name in self.sessions:
                    await self.disconnect_server(temp_server_name)
                if temp_server_name in self.servers:
                    self.remove_server(temp_server_name)
                print(f"DEBUG: test_local_server_capabilities: Cleaned up {temp_server_name}")
            except Exception as cleanup_error:
                print(f"Error cleaning up temporary server {temp_server_name}: {cleanup_error}")

    async def disconnect_server(self, name: str) -> bool:
        """Disconnect from an MCP server"""
        print("Attempting to disconnect from MCP server:", name)
        if name in self.sessions:
            print(f"DEBUG: Disconnecting from server {name} with session {self.sessions[name]}")
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
        else:
            print(f"No active session found for {name}. Trying to disconnect with {name} as server name.")
            if name in self.servers:
                await self.dynamic_commands.unregister_server_tools(name)
 
                self.servers[name].status = "disconnected"
                self.save_config()
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
        # Only save config for local servers
        if self._is_local_server(server):
            self.save_config()    
    def remove_server(self, name: str):
        """Remove a server configuration"""
        if name in self.servers:
            # Disconnect first if connected
            if name in self.sessions:
                asyncio.create_task(self.disconnect_server(name))
            
            del self.servers[name]
            self.save_config()
