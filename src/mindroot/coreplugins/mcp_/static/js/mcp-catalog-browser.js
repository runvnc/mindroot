import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class McpCatalogBrowser extends BaseEl {
  static properties = {
    catalogData: { type: Object },
    filteredServers: { type: Array },
    categories: { type: Array },
    selectedCategory: { type: String },
    searchTerm: { type: String },
    loading: { type: Boolean },
    stats: { type: Object }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .catalog-browser {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1400px;
      margin: 0 auto;
      gap: 20px;
    }

    .stats {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .stat-card {
      background: #2a2a40;
      padding: 15px;
      border-radius: 6px;
      text-align: center;
      min-width: 100px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .stat-number {
      font-size: 24px;
      font-weight: bold;
      color: #4fc3f7;
    }

    .stat-label {
      font-size: 12px;
      color: #bbb;
    }

    .filter-bar {
      display: flex;
      gap: 10px;
      margin-bottom: 15px;
      align-items: center;
      flex-wrap: wrap;
    }

    .filter-bar select,
    .filter-bar input {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
    }

    .filter-bar input {
      min-width: 200px;
    }

    .server-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 15px;
    }

    .server-card {
      background: #2a2a40;
      border-radius: 6px;
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      position: relative;
    }

    .server-card.running {
      border-color: #4caf50;
      box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
    }

    .server-card.installed {
      border-color: #ff9800;
    }

    .server-card h3 {
      margin-top: 0;
      color: #fff;
      padding-right: 80px;
    }

    .status {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: bold;
      position: absolute;
      top: 10px;
      right: 10px;
    }

    .status.running {
      background: #4caf50;
      color: white;
    }

    .status.installed {
      background: #ff9800;
      color: white;
    }

    .status.available {
      background: #757575;
      color: white;
    }

    .category-badge {
      background: #1976d2;
      color: white;
      padding: 2px 6px;
      border-radius: 3px;
      font-size: 10px;
      margin-right: 5px;
    }

    .tools-list {
      font-size: 12px;
      color: #bbb;
      margin-top: 5px;
    }

    .server-actions {
      margin-top: 10px;
      display: flex;
      gap: 5px;
      flex-wrap: wrap;
    }

    button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      transition: background 0.2s;
    }

    button:hover {
      background: #3a3a50;
    }

    button.success {
      background: #4caf50;
      border-color: #4caf50;
    }

    button.success:hover {
      background: #45a049;
    }

    button.danger {
      background: #f44336;
      border-color: #f44336;
    }

    button.danger:hover {
      background: #d32f2f;
    }

    button.primary {
      background: #1976d2;
      border-color: #1976d2;
    }

    button.primary:hover {
      background: #1565c0;
    }

    .loading {
      text-align: center;
      padding: 2rem;
      color: #888;
    }

    .message {
      padding: 10px;
      border-radius: 4px;
      margin: 10px 0;
    }

    .message.success {
      background: #4caf50;
      color: white;
    }

    .message.error {
      background: #f44336;
      color: white;
    }

    .message.info {
      background: #2196f3;
      color: white;
    }
  `;

  constructor() {
    super();
    this.catalogData = { servers: [], categories: [] };
    this.filteredServers = [];
    this.categories = [];
    this.selectedCategory = '';
    this.searchTerm = '';
    this.loading = false;
    this.stats = { total: 0, running: 0, installed: 0 };
    this.messages = [];
    this.loadCatalog();
  }
  async loadCatalog() {
    this.loading = true;
    try {
      const response = await fetch('/mr_mcp/api/catalog', {
        method: 'GET'
      });
      const result = await response.json();
      
      if (result.success) {
        this.catalogData = result.result;
        this.categories = result.result.categories || [];
        this.updateFilteredServers();
        this.updateStats();
      } else {
        this.showMessage('Error loading catalog: ' + result.error, 'error');
      }
    } catch (error) {
      this.showMessage('Error loading catalog: ' + error.message, 'error');
    }
    this.loading = false;
  }

  updateFilteredServers() {
    let filtered = this.catalogData.servers || [];
    
    if (this.selectedCategory) {
      filtered = filtered.filter(s => s.category === this.selectedCategory);
    }
    
    if (this.searchTerm) {
      const term = this.searchTerm.toLowerCase();
      filtered = filtered.filter(s => 
        s.name.toLowerCase().includes(term) ||
        s.display_name.toLowerCase().includes(term) ||
        s.description.toLowerCase().includes(term)
      );
    }
    
    this.filteredServers = filtered;
  }

  updateStats() {
    const servers = this.catalogData.servers || [];
    this.stats = {
      total: servers.length,
      running: servers.filter(s => s.running).length,
      installed: servers.filter(s => s.installed).length
    };
  }

  handleCategoryChange(e) {
    this.selectedCategory = e.target.value;
    this.updateFilteredServers();
  }

  handleSearchChange(e) {
    this.searchTerm = e.target.value;
    this.updateFilteredServers();
  }
  async installAndRun(serverName) {
    this.showMessage(`Installing and starting ${serverName}...`, 'info');
    
    try {
      const response = await fetch('/mr_mcp/api/catalog/install-and-run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: serverName})
      });
      const result = await response.json();
      
      if (result.success) {
        this.showMessage(result.result, 'success');
        await this.loadCatalog();
      } else {
        this.showMessage('Error: ' + result.error, 'error');
      }
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'error');
    }
  }

  async installOnly(serverName) {
    this.showMessage(`Installing ${serverName}...`, 'info');
    
    try {
      const response = await fetch('/mr_mcp/api/catalog/install', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: serverName})
      });
      const result = await response.json();
      
      if (result.success) {
        this.showMessage(result.result, 'success');
        await this.loadCatalog();
      } else {
        this.showMessage('Error: ' + result.error, 'error');
      }
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'error');
    }
  }

  async stopServer(serverName) {
    this.showMessage(`Stopping ${serverName}...`, 'info');
    
    try {
      const response = await fetch('/mr_mcp/api/catalog/stop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({server_name: serverName})
      });
      const result = await response.json();
      
      if (result.success) {
        this.showMessage(result.result, 'success');
        await this.loadCatalog();
      } else {
        this.showMessage('Error: ' + result.error, 'error');
      }
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'error');
    }
  }

  async showServerInfo(serverName) {
    try {
      const response = await fetch(`/mr_mcp/api/catalog/info/${serverName}`, {
        method: 'GET'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(JSON.stringify(result.result, null, 2));
      } else {
        this.showMessage('Error: ' + result.error, 'error');
      }
    } catch (error) {
      this.showMessage('Error: ' + error.message, 'error');
    }
  }
  showMessage(message, type) {
    // Create a temporary message element
    const messageEl = document.createElement('div');
    messageEl.className = `message ${type}`;
    messageEl.textContent = message;
    
    // Find the messages container or create one
    let messagesContainer = this.shadowRoot.querySelector('.messages');
    if (!messagesContainer) {
      messagesContainer = document.createElement('div');
      messagesContainer.className = 'messages';
      this.shadowRoot.appendChild(messagesContainer);
    }
    
    messagesContainer.appendChild(messageEl);
    
    // Remove message after 5 seconds
    setTimeout(() => {
      if (messageEl.parentNode) {
        messageEl.parentNode.removeChild(messageEl);
      }
    }, 5000);
  }

  _render() {
    if (this.loading) {
      return html`<div class="loading">Loading server catalog...</div>`;
    }

    return html`
      <div class="catalog-browser">
        <div class="stats">
          <div class="stat-card">
            <div class="stat-number">${this.stats.total}</div>
            <div class="stat-label">Total Servers</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.stats.running}</div>
            <div class="stat-label">Running</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.stats.installed}</div>
            <div class="stat-label">Installed</div>
          </div>
        </div>
        
        <div class="filter-bar">
          <select @change=${this.handleCategoryChange}>
            <option value="">All Categories</option>
            ${this.categories.map(category => html`
              <option value="${category}">
                ${category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            `)}
          </select>
          <input 
            type="text" 
            placeholder="Search servers..." 
            @input=${this.handleSearchChange}
          >
          <button class="primary" @click=${this.loadCatalog}>Refresh Status</button>
        </div>
        
        <div class="server-grid">
          ${this.filteredServers.length === 0 ? 
            html`<div class="loading">No servers found</div>` :
            this.filteredServers.map(server => {
              const statusClass = server.running ? 'running' : server.installed ? 'installed' : 'available';
              const statusText = server.running ? 'RUNNING' : server.installed ? 'INSTALLED' : 'AVAILABLE';
              const toolsList = server.tools.slice(0, 3).join(', ') + (server.tools.length > 3 ? '...' : '');
              
              return html`
                <div class="server-card ${statusClass}">
                  <span class="status ${statusClass}">${statusText}</span>
                  <h3>${server.display_name}</h3>
                  <p>${server.description}</p>
                  <div>
                    <span class="category-badge">${server.category}</span>
                    <span style="font-size: 12px; color: #bbb;">${server.install_method}</span>
                  </div>
                  <div class="tools-list">Tools: ${toolsList}</div>
                  <div class="server-actions">
                    ${server.running ? 
                      html`<button class="danger" @click=${() => this.stopServer(server.name)}>⏹ Stop</button>` :
                      html`<button class="success" @click=${() => this.installAndRun(server.name)}>🚀 Install & Run</button>`
                    }
                    ${!server.installed && !server.running ? 
                      html`<button @click=${() => this.installOnly(server.name)}>📦 Install Only</button>` : ''
                    }
                    <button @click=${() => this.showServerInfo(server.name)}>ℹ Info</button>
                  </div>
                </div>
              `;
            })
          }
        </div>
      </div>
    `;
  }
}

customElements.define('mcp-catalog-browser', McpCatalogBrowser);