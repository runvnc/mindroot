#!/usr/bin/env python3
"""
Test script to verify MCP server installation and connection fixes.

This script tests:
1. Config filtering (local vs remote servers)
2. Installation status tracking
3. Dynamic command registration
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the mindroot source to path
sys.path.insert(0, '/files/mindroot/src')

def test_config_filtering():
    """Test that only local servers are saved to config."""
    print("\n=== Testing Config Filtering ===")
    
    try:
        from mindroot.coreplugins.mcp_.mcp_manager import MCPManager, MCPServer
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config = f.name
        
        # Create manager with temp config
        manager = MCPManager()
        manager.config_file = Path(temp_config)
        
        # Create test servers
        local_server = MCPServer(
            name="test_local",
            description="Test local server",
            command="python",
            args=["-m", "test_server"],
            transport="stdio"
        )
        
        remote_server = MCPServer(
            name="test_remote",
            description="Test remote server",
            transport="http",
            url="https://example.com/mcp",
            auth_type="oauth2"
        )
        
        # Add servers
        manager.add_server("test_local", local_server)
        manager.add_server("test_remote", remote_server)
        
        print(f"Added servers: {list(manager.servers.keys())}")
        
        # Test filtering logic
        local_check = manager._is_local_server(local_server)
        remote_check = manager._is_local_server(remote_server)
        
        print(f"Local server check: {local_check} (should be True)")
        print(f"Remote server check: {remote_check} (should be False)")
        
        # Test config saving
        manager.save_config()
        
        # Read config file
        with open(temp_config, 'r') as f:
            saved_config = json.load(f)
        
        print(f"Saved servers: {list(saved_config.keys())}")
        
        # Verify only local server was saved
        if "test_local" in saved_config and "test_remote" not in saved_config:
            print("✅ Config filtering works correctly")
            return True
        else:
            print("❌ Config filtering failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            os.unlink(temp_config)
        except:
            pass

def test_installation_tracking():
    """Test installation status tracking."""
    print("\n=== Testing Installation Tracking ===")
    
    try:
        from mindroot.coreplugins.mcp_.mcp_manager import MCPManager, MCPServer
        
        manager = MCPManager()
        
        # Create test server
        test_server = MCPServer(
            name="test_server",
            description="Test server",
            command="python",
            args=["-m", "test_server"],
            transport="stdio"
        )
        
        # Add server
        manager.add_server("test_server", test_server)
        
        # Test marking as installed
        manager.mark_server_as_installed("test_server", "registry_123")
        
        # Check if server is marked as installed
        server = manager.servers["test_server"]
        if hasattr(server, 'installed') and server.installed:
            print("✅ Server marked as installed")
        else:
            print("❌ Server not marked as installed")
            return False
            
        if hasattr(server, 'registry_id') and server.registry_id == "registry_123":
            print("✅ Registry ID stored correctly")
            return True
        else:
            print("❌ Registry ID not stored")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dynamic_commands():
    """Test dynamic command registration system."""
    print("\n=== Testing Dynamic Commands ===")
    
    try:
        from mindroot.coreplugins.mcp_.dynamic_commands import MCPDynamicCommands
        
        # Create mock tool
        class MockTool:
            def __init__(self, name, description):
                self.name = name
                self.description = description
                self.inputSchema = {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Input text"}
                    },
                    "required": ["text"]
                }
        
        dynamic_commands = MCPDynamicCommands()
        
        # Create mock tools
        tools = [
            MockTool("test_tool_1", "Test tool 1"),
            MockTool("test_tool_2", "Test tool 2")
        ]
        
        # Test command registration tracking
        server_commands = dynamic_commands.get_registered_commands_for_server("test_server")
        print(f"Commands for test_server: {server_commands}")
        
        print("✅ Dynamic commands system accessible")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("MCP Installation Fix Test Suite")
    print("=" * 40)
    
    tests = [
        test_config_filtering,
        test_installation_tracking,
        test_dynamic_commands
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
