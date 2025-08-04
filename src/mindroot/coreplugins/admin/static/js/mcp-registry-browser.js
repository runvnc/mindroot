import { BaseEl } from '/admin/static/js/base.js';
import { html, css } from '/admin/static/js/lit-core.min.js';

class McpRegistryBrowser extends BaseEl {
  static properties = {
    servers: { type: Array },
    categories: { type: Array },
    selectedCategory: { type: String },
    searchQuery: { type: String },
    loading: { type: Boolean },
    error: { type: String },
    success: { type: String },
    page: { type: Number },
    totalServers: { type: Number },
    oauthFlow: { type: Object },
    oauthWindow: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .registry-browser {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-width: 1200px;
      margin: 0 auto;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .search-controls {
      display: flex;
      gap: 1rem;
      align-items: center;
      flex-wrap: wrap;
    }

    .search-input {
      flex: 1;
      min-width: 200px;
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
    }

    .category-select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      min-width: 150px;
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

    button.primary {
      background: #4a9eff;
    }

    button.primary:hover {
      background: #3a8eef;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .server-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }

    .server-card {
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      padding: 1rem;
      transition: border-color 0.2s;
    }

    .server-card:hover {
      border-color: #4a9eff;
    }

    .server-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.5rem;
    }

    .server-title {
      font-weight: bold;
      color: #4a9eff;
      font-size: 1.1rem;
    }

    .server-type {
      background: rgba(74, 158, 255, 0.2);
      color: #4a9eff;
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-size: 0.8rem;
      text-transform: uppercase;
    }

    .server-type.remote {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
    }

    .server-description {
      color: #ccc;
      margin-bottom: 1rem;
      line-height: 1.4;
    }

    .server-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
      font-size: 0.9rem;
      color: #999;
    }

    .meta-item {
      background: rgba(255, 255, 255, 0.05);
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
    }

    .tools-count {
      color: #4a9eff;
      font-weight: bold;
    }

    .server-actions {
      display: flex;
      gap: 0.5rem;
      justify-content: flex-end;
    }

    .loading {
      text-align: center;
      color: #ccc;
      padding: 2rem;
    }

    .error {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }

    .success {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }

    .oauth-status {
      background: rgba(74, 158, 255, 0.2);
      color: #4a9eff;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }

    .empty-state {
      text-align: center;
      color: #999;
      padding: 3rem;
    }

    .empty-state h3 {
      color: #ccc;
      margin-bottom: 1rem;
    }
  `;

  constructor() {
    super();
    this.servers = [];
    this.categories = [];
    this.selectedCategory = '';
    this.searchQuery = '';
    this.loading = false;
    this.error = '';
    this.success = '';
    this.page = 1;
    this.totalServers = 0;
    this.oauthFlow = null;
    this.oauthWindow = null;
    
    this.loadCategories();
    this.loadServers();
    
    // Listen for OAuth callback messages
    window.addEventListener('message', this.handleOAuthCallback.bind(this));
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Clean up OAuth window if it exists
    if (this.oauthWindow && !this.oauthWindow.closed) {
      this.oauthWindow.close();
    }
    // Remove event listener
    window.removeEventListener('message', this.handleOAuthCallback.bind(this));
  }

  async loadCategories() {
    try {
      const response = await fetch('/admin/mcp/registry/categories');
      if (response.ok) {
        const data = await response.json();
        this.categories = data.categories || [];
      }
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  }

  async loadServers() {
    this.loading = true;
    this.error = '';
    
    try {
      const params = new URLSearchParams({
        page: this.page.toString(),
        limit: '12'
      });
      
      if (this.selectedCategory) {
        params.append('category', this.selectedCategory);
      }
      
      if (this.searchQuery.trim()) {
        params.append('search', this.searchQuery.trim());
      }
      
      const response = await fetch(`/admin/mcp/registry/browse?${params}`);
      
      if (response.ok) {
        const data = await response.json();
        this.servers = data.servers || [];
        this.totalServers = data.total || 0;
      } else {
        const errorData = await response.json();
        this.error = errorData.detail || 'Failed to load servers from registry';
      }
    } catch (error) {
      this.error = `Error loading servers: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  handleSearch() {
    this.page = 1;
    this.loadServers();
  }

  handleCategoryChange(e) {
    this.selectedCategory = e.target.value;
    this.page = 1;
    this.loadServers();
  }

  handleSearchInput(e) {
    this.searchQuery = e.target.value;
  }

  handleKeyPress(e) {
    if (e.key === 'Enter') {
      this.handleSearch();
    }
  }

  async installServer(server) {
    this.loading = true;
    this.error = '';
    this.success = '';
    this.oauthFlow = null;
    
    try {
      const response = await fetch('/admin/mcp/registry/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          registry_id: server.registry_id
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        this.success = data.message;
      } else if (data.requires_oauth) {
        // OAuth flow required
        this.oauthFlow = {
          auth_url: data.auth_url,
          flow_id: data.flow_id,
          server_name: data.server_name
        };
        this.success = data.message;
        
        // Automatically open OAuth window
        await this.startOAuthFlow();
      } else {
        this.error = data.detail || 'Installation failed';
      }
    } catch (error) {
      this.error = `Installation failed: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async startOAuthFlow() {
    if (!this.oauthFlow || !this.oauthFlow.auth_url) {
      this.error = 'No OAuth flow available';
      return;
    }

    this.success = 'Opening OAuth authorization window...';
    
    // Open OAuth window
    const width = 600;
    const height = 700;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    
    this.oauthWindow = window.open(
      this.oauthFlow.auth_url,
      'oauth_window',
      `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
    );

    if (!this.oauthWindow) {
      this.error = 'Failed to open OAuth window. Please allow popups and try again.';
      return;
    }

    // Monitor window closure
    const checkClosed = setInterval(() => {
      if (this.oauthWindow.closed) {
        clearInterval(checkClosed);
        if (this.oauthFlow) {
          this.error = 'OAuth window was closed before completion';
          this.oauthFlow = null;
        }
      }
    }, 1000);
  }

  async handleOAuthCallback(event) {
    // Only handle messages from our OAuth window
    if (!this.oauthWindow || event.source !== this.oauthWindow) {
      return;
    }

    if (event.data.type === 'oauth_callback' && event.data.code) {
      try {
        this.success = 'OAuth authorization received, completing installation...';
        
        // Close the OAuth window
        this.oauthWindow.close();
        this.oauthWindow = null;

        // Complete the OAuth flow
        const response = await fetch('/admin/mcp/registry/complete-oauth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            server_name: this.oauthFlow.server_name,
            code: event.data.code,
            state: event.data.state
          })
        });

        const data = await response.json();

        if (data.success) {
          this.success = data.message;
          this.oauthFlow = null;
        } else {
          throw new Error(data.detail || 'OAuth completion failed');
        }
      } catch (error) {
        this.error = `OAuth completion failed: ${error.message}`;
        this.oauthFlow = null;
      }
    }
  }

  _render() {
    return html`
      <div class="registry-browser">
        <div class="section">
          <h3>Browse MCP Servers from Registry</h3>
          
          ${this.error ? html`<div class="error">${this.error}</div>` : ''}
          ${this.success ? html`<div class="success">${this.success}</div>` : ''}
          ${this.oauthFlow ? html`<div class="oauth-status">OAuth flow in progress...</div>` : ''}
          
          <div class="search-controls">
            <input type="text" 
                   class="search-input"
                   placeholder="Search MCP servers..."
                   .value=${this.searchQuery}
                   @input=${this.handleSearchInput}
                   @keypress=${this.handleKeyPress}>
            
            <select class="category-select" 
                    .value=${this.selectedCategory}
                    @change=${this.handleCategoryChange}>
              <option value="">All Categories</option>
              ${this.categories.map(cat => html`<option value="${cat}">${cat}</option>`)}
            </select>
            
            <button class="primary" @click=${this.handleSearch} ?disabled=${this.loading}>
              Search
            </button>
          </div>

          ${this.loading ? html`<div class="loading">Loading servers...</div>` : ''}
          
          ${this.servers.length === 0 && !this.loading ? html`
            <div class="empty-state">
              <h3>No MCP Servers Found</h3>
              <p>Try adjusting your search criteria or check back later.</p>
            </div>
          ` : ''}
          
          ${this.servers.length > 0 ? html`
            <div class="server-grid">
              ${this.servers.map(server => this.renderServerCard(server))}
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  renderServerCard(server) {
    return html`
      <div class="server-card">
        <div class="server-header">
          <div class="server-title">${server.title}</div>
          <div class="server-type ${server.server_type}">${server.server_type}</div>
        </div>
        
        <div class="server-description">${server.description}</div>
        
        <div class="server-meta">
          <div class="meta-item">v${server.version}</div>
          <div class="meta-item">by ${server.author}</div>
          <div class="meta-item tools-count">${server.tools.length} tools</div>
          ${server.auth_type !== 'none' ? html`<div class="meta-item">Auth: ${server.auth_type}</div>` : ''}
        </div>
        
        <div class="server-actions">
          <button class="primary" 
                  @click=${() => this.installServer(server)}
                  ?disabled=${this.loading}>
            Install
          </button>
        </div>
      </div>
    `;
  }
}

customElements.define('mcp-registry-browser', McpRegistryBrowser);
