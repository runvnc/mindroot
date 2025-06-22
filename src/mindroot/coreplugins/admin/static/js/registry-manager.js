import { html } from '/admin/static/js/lit-core.min.js';
import { RegistryManagerBase } from './registry-manager-base.js';

class RegistryManager extends RegistryManagerBase {
  async checkAuthStatus() {
    if (this.authToken) {
      try {
        const response = await fetch(`${this.registryUrl}/stats`, {
          headers: {
            'Authorization': `Bearer ${this.authToken}`
          }
        });
        
        if (response.ok) {
          this.isLoggedIn = true;
        } else {
          this.logout();
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        this.logout();
      }
    }
  }

  async loadStats() {
    try {
      const response = await fetch(`${this.registryUrl}/stats`);
      if (response.ok) {
        this.stats = await response.json();
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  }

  async loadLocalContent() {
    try {
      const pluginsResponse = await fetch('/admin/plugin-manager/get-all-plugins');
      if (pluginsResponse.ok) {
        const pluginsData = await pluginsResponse.json();
        this.localPlugins = pluginsData.data || [];
      }

      const agentsResponse = await fetch('/admin/agents/local');
      if (agentsResponse.ok) {
        this.localAgents = await agentsResponse.json();
      }
    } catch (error) {
      console.error('Error loading local content:', error);
    }
  }

  async handleLogin() {
    const username = this.shadowRoot.getElementById('username').value;
    const password = this.shadowRoot.getElementById('password').value;
    
    if (!username || !password) {
      this.error = 'Please enter username and password';
      return;
    }
    
    await this.login(username, password);
  }

  async login(username, password) {
    this.loading = true;
    this.error = '';
    
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await fetch(`${this.registryUrl}/token`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        this.authToken = data.access_token;
        localStorage.setItem('registry_token', this.authToken);
        this.isLoggedIn = true;
        this.currentUser = { username };
      } else {
        const errorData = await response.json();
        this.error = errorData.detail || 'Login failed';
      }
    } catch (error) {
      this.error = 'Network error: ' + error.message;
    }
    
    this.loading = false;
  }

  logout() {
    this.authToken = null;
    this.isLoggedIn = false;
    this.currentUser = null;
    localStorage.removeItem('registry_token');
  }

  async search(query = this.searchQuery, category = this.selectedCategory) {
    this.loading = true;
    this.error = '';
    
    try {
      const params = new URLSearchParams({
        query: query || '',
        limit: '20',
        semantic: 'true'
      });
      
      if (category && category !== 'all') {
        params.append('category', category);
      }
      
      const response = await fetch(`${this.registryUrl}/search?${params}`);
      
      if (response.ok) {
        const data = await response.json();
        this.searchResults = data.results || [];
      } else {
        this.error = 'Search failed';
      }
    } catch (error) {
      this.error = 'Network error: ' + error.message;
    }
    
    this.loading = false;
  }

  async installFromRegistry(item) {
    this.loading = true;
    this.error = '';
    
    try {
      if (this.authToken) {
        await fetch(`${this.registryUrl}/install/${item.id}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.authToken}`
          }
        });
      }
      
      if (item.category === 'plugin') {
        await this.installPlugin(item);
      } else if (item.category === 'agent') {
        await this.installAgent(item);
      }
      
      await this.loadLocalContent();
      
    } catch (error) {
      this.error = 'Installation failed: ' + error.message;
    }
    
    this.loading = false;
  }

  async installPlugin(item) {
    const installData = {
      plugin: item.title,
      source: item.github_url ? 'github' : 'pypi',
      source_path: item.github_url || item.pypi_module
    };
    
    const response = await fetch('/admin/plugin-manager/stream-install-plugin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(installData)
    });
    
    if (!response.ok) {
      throw new Error('Plugin installation failed');
    }
  }

  async installAgent(item) {
    const agentData = {
      ...item.data,
      name: item.title,
      description: item.description
    };
    
    const response = await fetch('/admin/agents/local', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: `agent=${encodeURIComponent(JSON.stringify(agentData))}`
    });
    
    if (!response.ok) {
      throw new Error('Agent installation failed');
    }
  }

  _render() {
    return html`
      <div class="registry-manager">
        ${this.renderHeader()}
        ${this.renderTabs()}
        ${this.renderContent()}
      </div>
    `;
  }

  renderHeader() {
    if (this.isLoggedIn) {
      return html`
        <div class="user-info">
          <span>Logged in as: ${this.currentUser?.username}</span>
          <button @click=${this.logout}>Logout</button>
        </div>
      `;
    } else {
      return html`
        <div class="section">
          <h3>Registry Login</h3>
          <div class="login-form">
            <input type="text" placeholder="Username or Email" id="username">
            <input type="password" placeholder="Password" id="password">
            <button class="primary" @click=${this.handleLogin}>Login</button>
            ${this.error ? html`<div class="error">${this.error}</div>` : ''}
          </div>
        </div>
      `;
    }
  }

  renderTabs() {
    return html`
      <div class="tabs">
        <div class="tab ${this.activeTab === 'search' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'search'}>Search</div>
        <div class="tab ${this.activeTab === 'publish' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'publish'}>Publish</div>
        <div class="tab ${this.activeTab === 'stats' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'stats'}>Stats</div>
      </div>
    `;
  }

  renderContent() {
    switch (this.activeTab) {
      case 'search':
        return this.renderSearch();
      case 'publish':
        return this.renderPublish();
      case 'stats':
        return this.renderStats();
      default:
        return this.renderSearch();
    }
  }

  renderSearch() {
    return html`
      <div class="section">
        <h3>Search Registry</h3>
        <div class="search-form">
          <div class="form-row">
            <input type="text" placeholder="Search plugins and agents..." 
                   .value=${this.searchQuery}
                   @input=${(e) => this.searchQuery = e.target.value}>
            <select .value=${this.selectedCategory}
                    @change=${(e) => this.selectedCategory = e.target.value}>
              <option value="all">All</option>
              <option value="plugin">Plugins</option>
              <option value="agent">Agents</option>
            </select>
            <button class="primary" @click=${() => this.search()}>Search</button>
          </div>
        </div>
        
        ${this.loading ? html`<div class="loading">Searching...</div>` : ''}
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        
        <div class="search-results">
          ${this.searchResults.map(item => this.renderSearchResult(item))}
        </div>
      </div>
    `;
  }

  renderSearchResult(item) {
    return html`
      <div class="result-item">
        <div class="result-header">
          <h4 class="result-title">${item.title}</h4>
          <span class="result-version">v${item.version}</span>
        </div>
        <p class="result-description">${item.description}</p>
        <div class="result-meta">
          <span>Category: ${item.category}</span>
          <span>Downloads: ${item.download_count || 0}</span>
          <span>Rating: ${item.rating || 0}/5</span>
        </div>
        ${item.tags && item.tags.length > 0 ? html`
          <div class="result-tags">
            ${item.tags.map(tag => html`<span class="tag">${tag}</span>`)}
          </div>
        ` : ''}
        <div class="result-actions">
          <button class="success" @click=${() => this.installFromRegistry(item)}>Install</button>
          ${item.github_url ? html`<a href="${item.github_url}" target="_blank"><button>GitHub</button></a>` : ''}
        </div>
      </div>
    `;
  }

  renderPublish() {
    if (!this.isLoggedIn) {
      return html`
        <div class="section">
          <h3>Publish to Registry</h3>
          <p>Please log in to publish plugins and agents to the registry.</p>
        </div>
      `;
    }

    return html`
      <div class="section">
        <h3>Publish to Registry</h3>
        <p>Select a local plugin or agent to publish:</p>
        
        <h4>Local Plugins</h4>
        ${this.localPlugins.map(plugin => html`
          <div class="result-item">
            <h5>${plugin.name}</h5>
            <p>${plugin.description || 'No description'}</p>
            <button class="primary" @click=${() => this.publishItem(plugin, 'plugin')}>Publish Plugin</button>
          </div>
        `)}
        
        <h4>Local Agents</h4>
        ${this.localAgents.map(agent => html`
          <div class="result-item">
            <h5>${agent.name}</h5>
            <button class="primary" @click=${() => this.publishItem(agent, 'agent')}>Publish Agent</button>
          </div>
        `)}
      </div>
    `;
  }

  renderStats() {
    return html`
      <div class="section">
        <h3>Registry Statistics</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">${this.stats.total_plugins || 0}</div>
            <div class="stat-label">Plugins</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.stats.total_agents || 0}</div>
            <div class="stat-label">Agents</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.stats.total_users || 0}</div>
            <div class="stat-label">Users</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.stats.total_installs || 0}</div>
            <div class="stat-label">Installs</div>
          </div>
        </div>
      </div>
    `;
  }

  async publishItem(item, type) {
    // Implementation for publishing items to registry
    console.log('Publishing', type, item);
    // This would involve creating the proper payload and sending to registry
  }
}

customElements.define('registry-manager', RegistryManager);
