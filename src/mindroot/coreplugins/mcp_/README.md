# MindRoot MCP Integration Plugin

This plugin integrates the Model Context Protocol (MCP) with MindRoot, allowing the AI to connect to and use MCP servers for enhanced capabilities.

## Features

- **MCP Client**: Connect to MCP servers via stdio, SSE, or WebSocket
- **Server Management**: Add, configure, and manage MCP servers
- **uvx/npx Support**: Easy installation and running of MCP servers via uvx (Python) and npx (Node.js)
- **Tool Integration**: Use MCP tools as MindRoot commands
- **Resource Access**: Read resources from MCP servers
- **Admin Interface**: Web UI for managing MCP servers
- **Server Discovery**: Discover available MCP servers from online directories

## Installation

1. Install the MCP Python SDK and optional tools:
```bash
pip install mcp
```
   For uvx support: `pip install uvx`
   For npx support: Install Node.js and npm

2. Install the plugin:
```bash
cd /xfiles/update_plugins/mr_mcp
pip install -e .
```

3. Enable the plugin commands in the MindRoot admin interface

## Usage

### Admin Interface

Access the MCP management interface at `/admin` and look for the "MCP Servers" section.

### Commands

- `mcp_list_servers` - List all configured MCP servers
- `mcp_connect` - Connect to an MCP server
- `mcp_disconnect` - Disconnect from an MCP server
- `mcp_install_uvx_server` - Install and configure a uvx-based MCP server
- `mcp_install_npx_server` - Install and configure an npx-based MCP server
- `mcp_list_tools` - List available tools from MCP servers
- `mcp_call_tool` - Call a tool on an MCP server
- `mcp_list_resources` - List available resources
- `mcp_read_resource` - Read a resource from an MCP server
- `mcp_discover_servers` - Discover available MCP servers
- `mcp_install_server` - Configure a new MCP server

### Example Usage

```json
// Install a uvx-based server (Python)
{ "mcp_install_uvx_server": {
    "name": "calculator",
    "package": "mcp-server-calculator",
    "description": "Calculator server"
}}

// Install an npx-based server (Node.js)
{ "mcp_install_npx_server": {
    "name": "github",
    "package": "@modelcontextprotocol/server-github",
    "description": "GitHub integration server"
}}

// Configure a filesystem server
{ "mcp_install_server": {
    "name": "filesystem",
    "description": "File system operations",
    "command": "python",
    "args": ["-m", "mcp.server.filesystem"]
}}

// Connect to the server
{ "mcp_connect": { "server_name": "filesystem" } }

// List available tools
{ "mcp_list_tools": {} }

// Call a tool
{ "mcp_call_tool": {
    "server_name": "filesystem",
    "tool_name": "read_file",
    "arguments": {"path": "/tmp/test.txt"}
}}
```

## Popular MCP Servers

- **Calculator** (uvx): `mcp-server-calculator` - Mathematical calculations
- **Filesystem** (Python): File operations
- **GitHub** (npx): `@modelcontextprotocol/server-github` - GitHub API integration
- **Brave Search** (npx): `@modelcontextprotocol/server-brave-search` - Web search
- **SQLite** (npx): `@modelcontextprotocol/server-sqlite` - Database operations
- **Slack** (npx): `@modelcontextprotocol/server-slack` - Slack integration
- **Google Drive** (npx): `@modelcontextprotocol/server-gdrive` - Google Drive access
- **Puppeteer** (npx): `@modelcontextprotocol/server-puppeteer` - Web automation

See the discovery feature to find more available servers.

## Architecture

- `MCPManager`: Core class managing server connections
- `MCPServer`: Pydantic model for server configuration
- Commands: MindRoot commands for MCP operations
- Admin UI: Web interface for server management
- Router: FastAPI routes for the admin interface

## Configuration

Server configurations are stored in `/tmp/mcp_servers.json` and include:
- Server name and description
- Command and arguments
- Transport type (stdio, SSE, WebSocket)
- Connection status
- Available capabilities (tools, resources, prompts)

## Development

The plugin supports multiple installation methods:
- **uvx**: For Python-based MCP servers (similar to pipx)
- **npx**: For Node.js-based MCP servers
- **pip**: For Python packages
- **npm**: For Node.js packages
- **manual**: For custom installations

To extend the plugin:
1. Add new commands in `mod.py`
2. Update the admin interface in `templates/mcp_admin.jinja2`
3. Add new server discovery sources
4. Implement additional transport types

## Troubleshooting

- Ensure MCP SDK is installed: `pip install mcp`
- For uvx servers: Install uvx with `pip install uvx`
- For npx servers: Ensure Node.js and npm are installed
- Check server command paths and arguments
- Verify server processes are running
- Check logs for connection errors
- Ensure proper permissions for server executables