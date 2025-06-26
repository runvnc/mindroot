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

  async handleRegister() {
    const username = this.shadowRoot.getElementById('reg-username').value;
    const email = this.shadowRoot.getElementById('reg-email').value;
    const password = this.shadowRoot.getElementById('reg-password').value;
    const confirmPassword = this.shadowRoot.getElementById('reg-confirm-password').value;
    
    if (!username || !email || !password || !confirmPassword) {
      this.error = 'Please fill in all fields';
      return;
    }
    
    if (password !== confirmPassword) {
      this.error = 'Passwords do not match';
      return;
    }
    
    await this.register(username, email, password);
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
        ${this.renderSettings()}
        ${this.renderHeader()}
        ${this.renderTabs()}
        ${this.renderContent()}
      </div>
    `;
  }

  renderSettings() {
    return html`
      <details class="settings-section">
        <summary>
          <span class="material-icons">settings</span>
          <span>Settings</span>
        </summary>
        <div class="section">
          <h4>Registry Configuration</h4>
          <div class="form-row">
            <label>Registry URL:</label>
            <input type="url" 
                   .value=${this.registryUrl}
                   placeholder="http://localhost:8000"
                   @change=${(e) => this.updateRegistryUrl(e.target.value)}>
            <button @click=${() => this.testConnection()}>Test</button>
          </div>
          <p class="help-text">
            Default: http://localhost:8000 or MR_REGISTRY_URL environment variable
          </p>
        </div>
      </details>
    `;
  }

  renderHeader() {
    if (this.isLoggedIn) {
      return html`
        <div class="user-info">
          <span>Logged in: ${this.currentUser?.username}</span>
          <span>Registry: ${this.registryUrl}</span>
          <button @click=${this.logout}>Logout</button>
        </div>
      `;
    } else {
      return html`
        <div class="section">
          <h3>Registry Access</h3>
          <p>Registry: ${this.registryUrl}</p>
          
          ${this.showRegisterForm ? this.renderRegisterForm() : this.renderLoginForm()}
          
          <div class="auth-toggle">
            ${this.showRegisterForm ? 
              html`<button @click=${() => { this.showRegisterForm = false; this.error = ''; }}>Back to Login</button>` :
              html`<button @click=${() => { this.showRegisterForm = true; this.error = ''; }}>Create Account</button>`
            }
          </div>
          
          ${this.error ? html`<div class="${this.error.includes('successful') ? 'success' : 'error'}">${this.error}</div>` : ''}
        </div>
      `;
    }
  }

  renderLoginForm() {
    return html`
      <div class="login-form">
        <h4>Login</h4>
        <input type="text" placeholder="Username or Email" id="username">
        <input type="password" placeholder="Password" id="password">
        <button class="primary" @click=${this.handleLogin}>Login</button>
      </div>
    `;
  }

  renderRegisterForm() {
    return html`
      <div class="login-form">
        <h4>Create Account</h4>
        <input type="text" placeholder="Username" id="reg-username">
        <input type="email" placeholder="Email" id="reg-email">
        <input type="password" placeholder="Password" id="reg-password">
        <input type="password" placeholder="Confirm Password" id="reg-confirm-password">
        <button class="primary" @click=${this.handleRegister}>Register</button>
      </div>
    `;
  }

  renderTabs() {
    return html`
      <div class="tabs">
        <div class="tab ${this.activeTab === 'search' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'search'}>Search</div>
        <div class="tab ${this.activeTab === 'stats' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'stats'}>Stats</div>
      </div>
    `;
  }

  renderContent() {
    switch (this.activeTab) {
      case 'search':
        return this.renderSearch();
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
            <input type="text" placeholder="Search..." 
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
        ${this.error && !this.error.includes('successful') ? html`<div class="error">${this.error}</div>` : ''}
        
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
        <div class="result-actions">
          <button class="success" @click=${() => this.installFromRegistry(item)}>Install</button>
        </div>
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
    console.log('Publishing', type, item);
  }
}

customElements.define('registry-manager', RegistryManager);
