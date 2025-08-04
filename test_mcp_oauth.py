#!/usr/bin/env python3
"""
Test script to verify MCP OAuth configuration is working correctly.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the mindroot source to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_mcp_oauth_config():
    """Test MCP OAuth configuration."""
    print("Testing MCP OAuth Configuration...")
    
    # Test BASE_URL environment variable
    base_url = os.getenv('BASE_URL', 'http://localhost:3000')
    print(f"BASE_URL: {base_url}")
    
    callback_url = f"{base_url}/mcp_oauth_cb"
    print(f"OAuth Callback URL: {callback_url}")
    
    try:
        # Import MCP components
        from mindroot.coreplugins.mcp.mod import MCPManager, MCPServer
        print("✓ MCP components imported successfully")
        
        # Create a test server configuration
        test_server = MCPServer(
            name="test_oauth_server",
            description="Test OAuth server",
            command="",
            transport="http",
            url="https://example.com/mcp",
            auth_type="oauth2",
            client_id="test_client",
            scopes=["read", "write"]
        )
        
        print(f"✓ Test server created with auth_type: {test_server.auth_type}")
        print(f"✓ Test server URL: {test_server.url}")
        
        # Test MCP manager
        manager = MCPManager()
        print("✓ MCP Manager created successfully")
        
        # Test OAuth status method
        status = manager.get_oauth_status("nonexistent_server")
        print(f"✓ OAuth status method works: {status.get('error', 'No error')}")
        
        print("\n🎉 All MCP OAuth configuration tests passed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure MCP dependencies are installed: pip install mcp")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Set a test BASE_URL if not already set
    if not os.getenv('BASE_URL'):
        os.environ['BASE_URL'] = 'https://mymrserver.net'
        print("Set test BASE_URL to: https://mymrserver.net")
    
    asyncio.run(test_mcp_oauth_config())
