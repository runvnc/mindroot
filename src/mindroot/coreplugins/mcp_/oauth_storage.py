"""OAuth token storage implementation for MCP servers."""

from typing import Optional
from datetime import datetime
import json

try:
    from mcp.client.auth import TokenStorage
    from mcp.shared.auth import OAuthToken, OAuthClientInformationFull
except ImportError:
    # Fallback if MCP not available
    class TokenStorage:
        pass
    OAuthToken = None
    OAuthClientInformationFull = None


class MCPTokenStorage(TokenStorage):
    """Token storage implementation for MCP OAuth flows.
    
    Stores tokens and client information in the MCP server configuration.
    """
    
    def __init__(self, server_name: str, mcp_manager):
        self.server_name = server_name
        self.mcp_manager = mcp_manager
    
    async def get_tokens(self) -> Optional[OAuthToken]:
        """Get stored OAuth tokens for the server."""
        if OAuthToken is None:
            return None
            
        if self.server_name not in self.mcp_manager.servers:
            return None
        
        server = self.mcp_manager.servers[self.server_name]
        
        if not server.access_token:
            return None
        
        # Parse token expiration
        expires_at = None
        if server.token_expires_at:
            try:
                expires_at = datetime.fromisoformat(server.token_expires_at.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        return OAuthToken(
            access_token=server.access_token,
            refresh_token=server.refresh_token,
            expires_at=expires_at,
            scope=" ".join(server.scopes) if server.scopes else None
        )
    
    async def set_tokens(self, tokens: OAuthToken) -> None:
        """Store OAuth tokens for the server."""
        if self.server_name not in self.mcp_manager.servers:
            return
        
        server = self.mcp_manager.servers[self.server_name]
        
        # Update server with token information
        server.access_token = tokens.access_token
        server.refresh_token = tokens.refresh_token
        
        if hasattr(tokens, 'expires_at') and tokens.expires_at:
            server.token_expires_at = tokens.expires_at.isoformat()
        elif hasattr(tokens, 'expires_in') and tokens.expires_in:
            # Calculate expires_at from expires_in
            from datetime import datetime, timedelta
            expires_at = datetime.now() + timedelta(seconds=tokens.expires_in)
            server.token_expires_at = expires_at.isoformat()
        else:
            server.token_expires_at = None
        
        if tokens.scope:
            server.scopes = tokens.scope.split(" ")
        
        # Save configuration
        self.mcp_manager.save_config()
    
    async def get_client_info(self) -> Optional[OAuthClientInformationFull]:
        """Get stored OAuth client information."""
        if OAuthClientInformationFull is None:
            return None
            
        if self.server_name not in self.mcp_manager.servers:
            return None
        
        server = self.mcp_manager.servers[self.server_name]
        
        if not server.client_id:
            return None
        
        # Create client info from server configuration
        client_info_data = {
            "client_id": server.client_id,
            "client_name": f"MindRoot MCP Client - {server.name}",
            "redirect_uris": [server.redirect_uri] if server.redirect_uri else [],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "scope": " ".join(server.scopes) if server.scopes else "user"
        }
        
        if server.client_secret:
            client_info_data["client_secret"] = server.client_secret
        
        return OAuthClientInformationFull(**client_info_data)
    
    async def set_client_info(self, client_info: OAuthClientInformationFull) -> None:
        """Store OAuth client information."""
        if self.server_name not in self.mcp_manager.servers:
            return
        
        server = self.mcp_manager.servers[self.server_name]
        
        # Update server with client information
        server.client_id = client_info.client_id
        
        if hasattr(client_info, 'client_secret') and client_info.client_secret:
            server.client_secret = client_info.client_secret
        
        if client_info.redirect_uris:
            server.redirect_uri = client_info.redirect_uris[0]
        
        if client_info.scope:
            server.scopes = client_info.scope.split(" ")
        
        # Save configuration
        self.mcp_manager.save_config()
    
    def clear_tokens(self):
        """Clear stored tokens for the server."""
        if self.server_name not in self.mcp_manager.servers:
            return
        
        server = self.mcp_manager.servers[self.server_name]
        server.access_token = None
        server.refresh_token = None
        server.token_expires_at = None
        
        # Save configuration
        self.mcp_manager.save_config()
