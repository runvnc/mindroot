import { BaseEl } from '/admin/static/js/base.js';
import { html, css } from '/admin/static/js/lit-core.min.js';

class McpManager extends BaseEl {
  static properties = {
    servers: { type: Array },
    catalog: { type: Object },
    loading: { type: Boolean },
    selectedTab: { type: String }
  };

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

    .tabs {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }

    .tab {
      padding: 0.5rem 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      color: #ccc;
    }

    .tab.active {
      background: #4a9eff;
      color: #fff;
    }

    .tab:hover {
      background: rgba(74, 158, 255, 0.3);
    }

    .server-list {
      display: grid;
      gap: 1rem;
    }

    .server-item {
      background: rgba(0, 0, 0, 0.2);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .server-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .server-name {
      font-weight: bold;
      color: #4a9eff;
    }

    .status-badge {
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-size: 0.8rem;
      text-transform: uppercase;
    }

    .status-badge.connected {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
    }

    .status-badge.disconnected {
      background: rgba(108, 117, 125, 0.2);
      color: #6c757d;
    }

    .status-badge.error {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
    }

    .server-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
    }

    button:hover {
      background: #3a3a50;
    }

    button.success {
      background: #28a745;
    }

    button.success:hover {
      background: #218838;
    }

    button.warning {
      background: #ffc107;
      color: #000;
    }

    button.warning:hover {
      background: #e0a800;
    }

    button.danger {
      background: #dc3545;
    }

    button.danger:hover {
      background: #c82333;
    }

    .loading {
      text-align: center;
      color: #ccc;
      padding: 2rem;
    }
  `;

  constructor() {
    super();
    this.servers = [];
    this.catalog = {};
    this.loading = false;
    this.selectedTab = 'servers';
    this.loadServers();
  }

  async loadServers() {
    this.loading = true;
    try {
      const response = await fetch('/admin/mcp/list');
      if (response.ok) {
        const data = await response.json();
        this.servers = data.data || [];
      }
    } catch (error) {
      console.error('Error loading MCP servers:', error);
    }
    this.loading = false;
  }

  async loadCatalog() {
    this.loading = true;
    try {
      const response = await fetch('/admin/mcp/catalog');
      if (response.ok) {
        const data = await response.json();
        this.catalog = data.data || {};
      }
    } catch (error) {
      console.error('Error loading MCP catalog:', error);
    }
    this.loading = false;
  }

  async connectServer(serverName) {
    try {
      const response = await fetch('/admin/mcp/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        await this.loadServers();
      }
    } catch (error) {
      console.error('Error connecting server:', error);
    }
  }

  async disconnectServer(serverName) {
    try {
      const response = await fetch('/admin/mcp/disconnect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        await this.loadServers();
      }
    } catch (error) {
      console.error('Error disconnecting server:', error);
    }
  }

  async removeServer(serverName) {
    if (!confirm(`Are you sure you want to remove the MCP server '${serverName}'?`)) return;
    
    try {
      const response = await fetch('/admin/mcp/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        await this.loadServers();
      }
    } catch (error) {
      console.error('Error removing server:', error);
    }
  }

  selectTab(tab) {
    this.selectedTab = tab;
    if (tab === 'catalog' && Object.keys(this.catalog).length === 0) {
      this.loadCatalog();
    }
  }

  _render() {
    return html`
      <div class="mcp-manager">
        <div class="section">
          <h3>MCP Server Management</h3>
          
          <div class="tabs">
            <div class="tab ${this.selectedTab === 'servers' ? 'active' : ''}" 
                 @click=${() => this.selectTab('servers')}>Local Servers</div>
            <div class="tab ${this.selectedTab === 'catalog' ? 'active' : ''}" 
                 @click=${() => this.selectTab('catalog')}>Server Catalog</div>
          </div>

          ${this.loading ? html`<div class="loading">Loading...</div>` : ''}
          
          ${this.selectedTab === 'servers' ? this.renderServers() : this.renderCatalog()}
        </div>
      </div>
    `;
  }

  renderServers() {
    if (this.servers.length === 0) {
      return html`<p>No MCP servers configured. Use the catalog to install some.</p>`;
    }

    return html`
      <div class="server-list">
        ${this.servers.map(server => html`
          <div class="server-item">
            <div class="server-header">
              <div class="server-name">${server.name}</div>
              <div class="status-badge ${server.status}">${server.status}</div>
            </div>
            <div class="server-description">${server.description}</div>
            <div class="server-meta">
              <small>Transport: ${server.transport} | Command: ${server.command}</small>
            </div>
            <div class="server-actions">
              ${server.status === 'connected' 
                ? html`<button class="warning" @click=${() => this.disconnectServer(server.name)}>Disconnect</button>`
                : html`<button class="success" @click=${() => this.connectServer(server.name)}>Connect</button>`
              }
              <button class="danger" @click=${() => this.removeServer(server.name)}>Remove</button>
            </div>
          </div>
        `)}
      </div>
    `;
  }

  renderCatalog() {
    const servers = this.catalog.servers || {};
    const serverList = Object.entries(servers);

    if (serverList.length === 0) {
      return html`<p>No servers in catalog. Loading...</p>`;
    }

    return html`
      <div class="server-list">
        ${serverList.map(([name, server]) => html`
          <div class="server-item">
            <div class="server-header">
              <div class="server-name">${server.display_name || name}</div>
              <div class="status-badge ${server.installed ? 'connected' : 'disconnected'}">
                ${server.installed ? 'Installed' : 'Available'}
              </div>
            </div>
            <div class="server-description">${server.description}</div>
            <div class="server-actions">
              ${server.installed 
                ? html`<button disabled>Already Installed</button>`
                : html`<button class="success" @click=${() => this.installFromCatalog(name)}>Install</button>`
              }
            </div>
          </div>
        `)}
      </div>
    `;
  }

  async installFromCatalog(serverName) {
    try {
      const response = await fetch('/admin/mcp/catalog/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        await this.loadServers();
        await this.loadCatalog();
      }
    } catch (error) {
      console.error('Error installing from catalog:', error);
    }
  }
}

customElements.define('mcp-manager', McpManager);
