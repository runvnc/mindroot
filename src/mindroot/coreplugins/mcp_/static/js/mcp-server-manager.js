import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class McpServerManager extends BaseEl {
  static properties = {
    servers: { type: Array },
    tools: { type: Array },
    discoveredServers: { type: Array },
    loading: { type: Boolean }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .mcp-manager {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      gap: 20px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section h2 {
      color: #4fc3f7;
      margin-top: 0;
      margin-bottom: 1rem;
    }

    .form-row {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
      flex-wrap: wrap;
    }

    .form-row input {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      min-width: 150px;
    }

    .server-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 15px;
      margin-top: 1rem;
    }

    .server-card {
      background: #2a2a40;
      border-radius: 6px;
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .server-card h3 {
      margin-top: 0;
      color: #fff;
    }

    .status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
      display: inline-block;
      margin: 5px 0;
    }

    .status.connected {
      background: #4caf50;
      color: white;
    }

    .status.disconnected {
      background: #757575;
      color: white;
    }

    .status.error {
      background: #f44336;
      color: white;
    }

    button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      margin: 4px;
      transition: background 0.2s;
    }

    button:hover {
      background: #3a3a50;
    }

    button.primary {
      background: #1976d2;
      border-color: #1976d2;
    }

    button.primary:hover {
      background: #1565c0;
    }

    button.danger {
      background: #f44336;
      border-color: #f44336;
    }

    button.danger:hover {
      background: #d32f2f;
    }

    .tools-list {
      margin-top: 1rem;
    }

    .tool-item {
      background: #2a2a40;
      padding: 10px;
      margin: 5px 0;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .tool-item strong {
      color: #4fc3f7;
    }

    .discovered-servers {
      margin-top: 1rem;
    }

    .discovered-server {
      background: #2a2a40;
      padding: 10px;
      margin: 5px 0;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .loading {
      text-align: center;
      padding: 2rem;
      color: #888;
    }
  `;

  constructor() {
    super();
    this.servers = [];
    this.tools = [];
    this.discoveredServers = [];
    this.loading = false;
    this.loadInitialData();
  }

  async loadInitialData() {
    this.loading = true;
    await Promise.all([
      this.loadServers(),
      this.loadTools()
    ]);
    this.loading = false;
  }

  async loadServers() {
    try {
      const response = await fetch('/mr_mcp/api/servers', {
        method: 'GET'
      });
      const result = await response.json();
      
      if (result.success && result.result) {
        this.servers = result.result;
      }
    } catch (error) {
      console.error('Error loading servers:', error);
    }
  }

  async loadTools() {
    try {
      const response = await fetch('/mr_mcp/api/tools', {
        method: 'GET'
      });
      const result = await response.json();
      
      if (result.success && result.result) {
        this.tools = result.result;
      }
    } catch (error) {
      console.error('Error loading tools:', error);
    }
  }

  async handleAddServer() {
    const name = this.getEl('#serverName').value;
    const description = this.getEl('#serverDesc').value;
    const command = this.getEl('#serverCmd').value;
    const argsStr = this.getEl('#serverArgs').value;
    const args = argsStr ? argsStr.split(',').map(s => s.trim()) : [];
    
    if (!name || !description || !command) {
      alert('Please fill in all required fields');
      return;
    }
    
    try {
      const response = await fetch('/mr_mcp/api/servers/install', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          name, description, command, args
        })
      });
      const result = await response.json();
      
      if (result.success) {
        this.getEl('#serverName').value = '';
        this.getEl('#serverDesc').value = '';
        this.getEl('#serverCmd').value = '';
        this.getEl('#serverArgs').value = '';
        await this.loadServers();
      } else {
        alert('Error adding server: ' + result.error);
      }
    } catch (error) {
      alert('Error adding server: ' + error.message);
    }
  }

  async handleConnectServer(name) {
    try {
      const response = await fetch('/mr_mcp/api/servers/connect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: name})
      });
      const result = await response.json();
      
      if (result.success) {
        await Promise.all([this.loadServers(), this.loadTools()]);
      } else {
        alert('Connection failed: ' + result.error);
      }
    } catch (error) {
      alert('Connection error: ' + error.message);
    }
  }

  async handleDisconnectServer(name) {
    try {
      const response = await fetch('/mr_mcp/api/servers/disconnect', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: name})
      });
      const result = await response.json();
      
      if (result.success) {
        await Promise.all([this.loadServers(), this.loadTools()]);
      } else {
        alert('Disconnect failed: ' + result.error);
      }
    } catch (error) {
      alert('Disconnect error: ' + error.message);
    }
  }

  async handleRemoveServer(name) {
    if (!confirm(`Are you sure you want to remove server "${name}"?`)) return;
    
    try {
      const response = await fetch('/api/command', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: 'mcp_remove_server', args: {server_name: name}})
      });
      const result = await response.json();
      
      if (result.success) {
        await this.loadServers();
      } else {
        alert('Remove failed: ' + result.error);
      }
    } catch (error) {
      alert('Remove error: ' + error.message);
    }
  }

  async handleDiscoverServers() {
    try {
      const response = await fetch('/mr_mcp/api/servers/discover', {
        method: 'GET'
      });
      const result = await response.json();
      
      if (result.success && result.result) {
        this.discoveredServers = result.result;
      }
    } catch (error) {
      console.error('Error discovering servers:', error);
    }
  }

  handleInstallDiscovered(server) {
    this.getEl('#serverName').value = server.name;
    this.getEl('#serverDesc').value = server.description;
    this.getEl('#serverCmd').value = server.command;
    this.getEl('#serverArgs').value = server.args.join(', ');
  }

  _render() {
    if (this.loading) {
      return html`<div class="loading">Loading MCP servers...</div>`;
    }

    return html`
      <div class="mcp-manager">
        <div class="section">
          <h2>Add New Server</h2>
          <div class="form-row">
            <input type="text" id="serverName" placeholder="Server Name">
            <input type="text" id="serverDesc" placeholder="Description">
            <input type="text" id="serverCmd" placeholder="Command">
            <input type="text" id="serverArgs" placeholder="Args (comma-separated)">
            <button class="primary" @click=${this.handleAddServer}>Add Server</button>
          </div>
        </div>
        
        <div class="section">
          <h2>Discover Servers</h2>
          <button @click=${this.handleDiscoverServers}>Discover Available Servers</button>
          <div class="discovered-servers">
            ${this.discoveredServers.map(server => html`
              <div class="discovered-server">
                <strong>${server.name}</strong> - ${server.description}<br>
                Command: ${server.command} ${server.args.join(' ')}<br>
                <button @click=${() => this.handleInstallDiscovered(server)}>Use This Config</button>
              </div>
            `)}
          </div>
        </div>
        
        <div class="section">
          <h2>Configured Servers</h2>
          <div class="server-grid">
            ${this.servers.map(server => html`
              <div class="server-card">
                <h3>${server.name}</h3>
                <p>${server.description}</p>
                <p>Transport: ${server.transport}</p>
                <p>Tools: ${server.tools_count} | Resources: ${server.resources_count}</p>
                <span class="status ${server.status}">${server.status.toUpperCase()}</span>
                <div>
                  ${server.status === 'disconnected' ? 
                    html`<button class="primary" @click=${() => this.handleConnectServer(server.name)}>Connect</button>` :
                    html`<button @click=${() => this.handleDisconnectServer(server.name)}>Disconnect</button>`
                  }
                  <button class="danger" @click=${() => this.handleRemoveServer(server.name)}>Remove</button>
                </div>
              </div>
            `)}
          </div>
        </div>
        
        <div class="section">
          <h2>Available Tools</h2>
          <div class="tools-list">
            ${this.tools.map(tool => html`
              <div class="tool-item">
                <strong>${tool.server}:${tool.name}</strong><br>
                ${tool.description || 'No description'}
              </div>
            `)}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('mcp-server-manager', McpServerManager);