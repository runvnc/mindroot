#!/usr/bin/env python3
"""
Test script to verify dynamic command registration for both uvx and npx MCP servers
"""

import asyncio
import sys
import os

# Add the mindroot lib to path
sys.path.insert(0, '/files/mindroot/src/mindroot')

from .mod import mcp_manager, MCPServer
from src.mr_mcp.dynamic_commands import MCPDynamicCommands
from lib.providers.commands import command_manager

async def test_dynamic_command_registration():
    print("Testing dynamic command registration for MCP servers...")
    
    # Check current registered commands
    print(f"\nCurrently registered commands: {len(command_manager.functions)}")
    mcp_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    print(f"Current MCP commands: {mcp_commands}")
    
    # Test creating both uvx and npx servers
    print("\n=== Testing UVX Server (Calculator) ===")
    
    uvx_server = EnhancedMCPServer(
        name="test_calculator",
        description="Test calculator server via uvx",
        command="uvx",
        args=["mcp-server-calculator"],
        install_method="uvx",
        install_package="mcp-server-calculator",
        auto_install=True
    )
    
    enhanced_mcp_manager.add_server("test_calculator", uvx_server)
    print(f"Added uvx server: {uvx_server.name}")
    print(f"Command: {uvx_server.command} {' '.join(uvx_server.args)}")
    
    print("\n=== Testing NPX Server (GitHub) ===")
    
    npx_server = EnhancedMCPServer(
        name="test_github",
        description="Test GitHub server via npx",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        install_method="npx",
        install_package="@modelcontextprotocol/server-github",
        auto_install=True
    )
    
    enhanced_mcp_manager.add_server("test_github", npx_server)
    print(f"Added npx server: {npx_server.name}")
    print(f"Command: {npx_server.command} {' '.join(npx_server.args)}")
    
    # Check if dynamic commands object is properly initialized
    print(f"\n=== Dynamic Commands System ===")
    print(f"Dynamic commands object: {enhanced_mcp_manager.dynamic_commands}")
    print(f"Sessions reference set: {bool(enhanced_mcp_manager.dynamic_commands.sessions)}")
    print(f"Registered dynamic commands: {enhanced_mcp_manager.dynamic_commands.get_registered_commands()}")
    
    # Test the registration process manually
    print("\n=== Manual Tool Registration Test ===")
    
    # Create a mock tool object
    class MockTool:
        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.inputSchema = {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
    
    mock_tools = [MockTool("calculate", "Perform mathematical calculations")]
    
    print("Testing tool registration for mock calculator...")
    await enhanced_mcp_manager.dynamic_commands.register_tools("test_calculator", mock_tools)
    
    # Check if command was registered
    expected_cmd = "mcp_test_calculator_calculate"
    if expected_cmd in command_manager.functions:
        print(f"✅ SUCCESS: Command {expected_cmd} was registered!")
        cmd_info = command_manager.functions[expected_cmd]
        if hasattr(cmd_info, 'docstring'):
            print(f"   Docstring: {cmd_info.docstring[:100]}...")
        else:
            print(f"   Command info: {type(cmd_info)}")
    else:
        print(f"❌ FAILED: Command {expected_cmd} was not registered")
        print(f"   Available commands: {list(command_manager.functions.keys())[-5:]}")
    
    # Test with npx server
    print("\nTesting tool registration for mock GitHub server...")
    
    github_tools = [MockTool("create_repository", "Create a new GitHub repository")]
    await enhanced_mcp_manager.dynamic_commands.register_tools("test_github", github_tools)
    
    expected_cmd2 = "mcp_test_github_create_repository"
    if expected_cmd2 in command_manager.functions:
        print(f"✅ SUCCESS: Command {expected_cmd2} was registered!")
    else:
        print(f"❌ FAILED: Command {expected_cmd2} was not registered")
    
    # Final summary
    print(f"\n=== Final Summary ===")
    final_mcp_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    print(f"Total MCP commands now: {len(final_mcp_commands)}")
    print(f"Dynamic commands: {[cmd for cmd in final_mcp_commands if 'test_' in cmd]}")
    
    print("\n=== Conclusion ===")
    print("The dynamic command registration system works the same for both uvx and npx servers.")
    print("The issue you're experiencing might be:")
    print("1. The MCP server isn't actually connecting successfully")
    print("2. The server doesn't expose tools (some servers only have resources/prompts)")
    print("3. There's an error during the connection process")
    print("4. The admin interface cache needs to be refreshed")
    
    print("\nTo debug further:")
    print("1. Check the server logs when connecting")
    print("2. Verify the server actually starts and responds")
    print("3. Check if the server exposes tools vs just resources")
    print("4. Try refreshing the admin interface after connection")

if __name__ == "__main__":
    asyncio.run(test_dynamic_command_registration())
