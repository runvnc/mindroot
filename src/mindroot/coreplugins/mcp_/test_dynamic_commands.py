"""
Test script to verify dynamic command registration for both uvx and npx MCP servers
"""
import asyncio
import sys
import os
sys.path.insert(0, '/files/mindroot/src/mindroot')
from .mod import mcp_manager, MCPServer
from src.mr_mcp.dynamic_commands import MCPDynamicCommands
from lib.providers.commands import command_manager

async def test_dynamic_command_registration():
    mcp_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
    uvx_server = EnhancedMCPServer(name='test_calculator', description='Test calculator server via uvx', command='uvx', args=['mcp-server-calculator'], install_method='uvx', install_package='mcp-server-calculator', auto_install=True)
    enhanced_mcp_manager.add_server('test_calculator', uvx_server)
    npx_server = EnhancedMCPServer(name='test_github', description='Test GitHub server via npx', command='npx', args=['-y', '@modelcontextprotocol/server-github'], install_method='npx', install_package='@modelcontextprotocol/server-github', auto_install=True)
    enhanced_mcp_manager.add_server('test_github', npx_server)

    class MockTool:

        def __init__(self, name, description):
            self.name = name
            self.description = description
            self.inputSchema = {'type': 'object', 'properties': {'expression': {'type': 'string', 'description': 'Mathematical expression to evaluate'}}, 'required': ['expression']}
    mock_tools = [MockTool('calculate', 'Perform mathematical calculations')]
    await enhanced_mcp_manager.dynamic_commands.register_tools('test_calculator', mock_tools)
    expected_cmd = 'mcp_test_calculator_calculate'
    if expected_cmd in command_manager.functions:
        cmd_info = command_manager.functions[expected_cmd]
    github_tools = [MockTool('create_repository', 'Create a new GitHub repository')]
    await enhanced_mcp_manager.dynamic_commands.register_tools('test_github', github_tools)
    expected_cmd2 = 'mcp_test_github_create_repository'
    final_mcp_commands = [name for name in command_manager.functions.keys() if name.startswith('mcp_')]
if __name__ == '__main__':
    asyncio.run(test_dynamic_command_registration())