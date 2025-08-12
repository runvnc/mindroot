/**
 * Registry Search Section
 * 
 * Handles search UI, category filtering, and results display
 * for the registry manager.
 */

import { html } from '/admin/static/js/lit-core.min.js';

class RegistrySearchSection {
  constructor(sharedState, mainComponent) {
    this.state = sharedState;
    this.main = mainComponent;
    this.services = null; // Will be set by main component
    this.searchTimeout = null;
  }

  setServices(services) {
    this.services = services;
  }

  // === Event Handlers ===

  handleSearchInput(e) {
    this.main.searchQuery = e.target.value;
    
    // Clear existing timeout
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
    
    // Set new timeout for auto-search after 500ms of no typing
    this.searchTimeout = setTimeout(() => {
      this.services.search();
      this.main.requestUpdate();
    }, 500);
  }

  handleCategoryChange(category) {
    this.main.selectedCategory = category;
    this.services.search();
    this.main.requestUpdate();
  }

  async loadTopContent() {
    await this.services.loadTopContent();
    this.main.requestUpdate();
  }

  async installFromRegistry(item) {
    await this.services.installFromRegistry(item);
    this.main.requestUpdate();
  }

  // === Helper Methods ===

  getInstalledMcpServer(item) {
    if (!this.main.localMcpServers || this.main.localMcpServers.length === 0) {
      return null;
    }
    // Use a fuzzy match: check if the item's title contains the server's name.
    // This handles cases where title is "Calculator Server" and name is "calculator".
    const normalizedTitle = item.title.toLowerCase();
    return this.main.localMcpServers.find(s => 
      normalizedTitle.includes(s.name.toLowerCase())
    );
  }

  // === Render Methods ===

  renderSearch() {
    return html`
      <div class="section">
        <h3>Registry Browser</h3>
        ${this.renderSearchForm()}
        ${this.renderSearchStatus()}
        ${this.renderSearchResults()}
      </div>
    `;
  }

  renderSearchForm() {
    return html`
      <div class="search-form">
        <div class="form-row">
          <input type="text" placeholder="Search plugins and agents..." 
                 .value=${this.main.searchQuery}
                 @input=${(e) => this.handleSearchInput(e)}>
        </div>
        ${this.renderCategoryTabs()}
      </div>
    `;
  }

  renderCategoryTabs() {
    return html`
      <div class="category-tabs">
        <button class="category-tab ${this.main.selectedCategory === 'all' ? 'active' : ''}" 
                @click=${() => this.handleCategoryChange('all')}>
          <span class="material-icons">apps</span>
          All
        </button>
        <button class="category-tab ${this.main.selectedCategory === 'plugin' ? 'active' : ''}" 
                @click=${() => this.handleCategoryChange('plugin')}>
          <span class="material-icons">extension</span>
          Plugins
        </button>
        <button class="category-tab ${this.main.selectedCategory === 'agent' ? 'active' : ''}" 
                @click=${() => this.handleCategoryChange('agent')}>
          <span class="material-icons">smart_toy</span>
          Agents
        </button>
        <button class="category-tab ${this.main.selectedCategory === 'mcp_server' ? 'active' : ''}" 
                @click=${() => this.handleCategoryChange('mcp_server')}>
          <span class="material-icons">dns</span>
          MCP Servers
        </button>
      </div>
    `;
  }

  renderSearchStatus() {
    if (this.state.loading) {
      return html`<div class="loading">Searching...</div>`;
    }
    
    if (this.main.error) {
      return html`<div class="error">${this.main.error}</div>`;
    }
    
    return '';
  }

  renderSearchResults() {
    return html`
      <div class="search-results">
        ${this.main.searchResults.length === 0 && !this.state.loading ? html`
          <div class="no-results">
            <p>No items found. Try adjusting your search terms or check your connection to the registry.</p>
            <button @click=${() => this.loadTopContent()}>Load Popular Items</button>
          </div>
        ` : ''}
        ${this.main.searchResults.map(item => this.renderSearchResult(item))}
      </div>
    `;
  }

  renderSearchResult(item) {
    const installedServer = item.category === 'mcp_server' ? this.getInstalledMcpServer(item) : null;
    const isInstalled = !!installedServer;

    return html`
      <div class="result-item">
        ${this.renderResultAvatar(item)}
        <div class="result-content">
          ${this.renderSemanticBadge(item)}
          ${this.renderResultHeader(item, item.data?.auth_type === 'oauth2')}
          <p class="result-description">${item.description}</p>
          ${this.renderResultMeta(item)}
          ${this.renderResultTags(item)}
          ${this.renderResultActions(item, installedServer)}
        </div>
      </div>
    `;
  }

  renderResultAvatar(item) {
    if (item.category !== 'agent') return '';
    
    const hasAssets = item.data?.persona_data?.persona_assets;
    const hasHashes = item.data?.persona_data?.asset_hashes;
    
    if (hasAssets && (hasAssets.faceref || hasAssets.avatar)) {
      const asset = hasAssets.faceref || hasAssets.avatar;
      return html`
        <div class="result-avatar">
          <img src="data:${asset.type};base64,${asset.data}" 
               alt="${item.title} avatar" 
               class="agent-avatar-large"
               onerror="this.style.display='none'">
        </div>
      `;
    } else if (hasHashes && (hasHashes.faceref || hasHashes.avatar)) {
      const hash = hasHashes.faceref || hasHashes.avatar;
      return html`
        <div class="result-avatar">
          <img src="${this.state.registryUrl}/assets/${hash}" 
               alt="${item.title} avatar" 
               class="agent-avatar-large"
               onerror="this.style.display='none'">
        </div>
      `;
    }
    
    return '';
  }

  renderSemanticBadge(item) {
    if (!item.is_semantic) return '';
    
    return html`
      <div class="semantic-badge">
        <span class="material-icons">psychology</span>
        Semantic Match ${item.distance_score ? `(${(1 - item.distance_score).toFixed(2)})` : ''}
      </div>
    `;
  }

  renderResultHeader(item, requiresOAuth) {
    const hasAvatar = item.category === 'agent' && 
      (item.data?.persona_data?.persona_assets?.faceref || 
       item.data?.persona_data?.persona_assets?.avatar || 
       item.data?.persona_data?.asset_hashes?.faceref || 
       item.data?.persona_data?.asset_hashes?.avatar);

    return html`
      <div class="result-header">
        ${hasAvatar ? html`
          <div class="agent-name-with-face">${item.title}</div>
        ` : html`
          <h4 class="result-title">${item.title}</h4>
        `}
        <span class="result-version">v${item.version}</span>
        ${requiresOAuth ? html`
          <span class="oauth-badge" title="Requires OAuth 2.0 authentication">
            <span class="material-icons">security</span>
            OAuth 2.0
          </span>
        ` : ''}
      </div>
    `;
  }

  renderResultMeta(item) {
    return html`
      <div class="result-meta">
        <span>Category: ${item.category}</span>
        <span>Downloads: ${item.download_count || 0}</span>
        <span>Rating: ${item.rating || 0}/5</span>
      </div>
    `;
  }

  renderResultTags(item) {
    if (!item.tags || item.tags.length === 0) return '';
    
    return html`
      <div class="result-tags">
        ${item.tags.map(tag => html`<span class="tag">${tag}</span>`)}
      </div>
    `;
  }

  renderResultActions(item, installedServer) {
    const isMcp = item.category === 'mcp_server';
    const isInstalled = !!installedServer;

    return html`
      <div class="result-actions">
        ${isMcp ? 
          (isInstalled ? 
            this.renderInstalledMcpActions(installedServer) : 
            this.renderUninstalledMcpActions(item)
          ) : 
          (this.state.localPlugins.some(p => p.name === item.title) ? 
            html`<div class="installed-badge"><span class="material-icons">check_circle</span> Installed</div>` : 
            html`<button class="success" @click=${() => this.installFromRegistry(item)} ?disabled=${this.state.loading}>Install</button>`
          )
        }
        ${item.github_url ? html`
          <a href="${item.github_url}" target="_blank">
            <button>GitHub</button>
          </a>
        ` : ''}
      </div>
    `;
  }

  renderInstalledMcpActions(server) {
    return html`
      <div class="installed-badge">
        <span class="material-icons">check_circle</span> 
        ${server.status === 'connected' ? 'Connected' : 'Installed'}
      </div>
      ${server.status === 'connected' ? html`
        <button class="danger" @click=${() => this.main.toggleMcpServerConnection(server.name, false)} ?disabled=${this.state.loading}>
          Disconnect
        </button>
      ` : html`
        <button class="success" @click=${() => this.main.toggleMcpServerConnection(server.name, true)} ?disabled=${this.state.loading}>
          Connect
        </button>
      `}
      <button class="danger" @click=${() => this.main.removeMcpServer(server.name)} ?disabled=${this.state.loading}>
        Remove
      </button>
    `;
  }

  renderUninstalledMcpActions(item) {
    const requiresOAuth = item.data && item.data.auth_type === 'oauth2';
    return html`
      <button class="success" 
              @click=${() => this.installFromRegistry(item)} 
              ?disabled=${this.state.loading}>
        ${requiresOAuth ? 'Connect' : 'Install'}
      </button>
    `;
  }
}

export { RegistrySearchSection };
