import { html } from '/admin/static/js/lit-core.min.js';
import { RegistryManagerBase } from './registry-manager-base.js';

class RegistryManager extends RegistryManagerBase {
  constructor() {
    super();
    this.searchTimeout = null;
  }

  // Return true if an agent with this name is already present in localAgents
  isAgentInstalled(name) {
    return (this.localAgents || []).some(a => a.name === name);
  }

  async checkAuthStatus() {
    if (this.authToken) {
      try {
        // First check if we can get user info
        const response = await fetch(`${this.registryUrl}/stats`, {
          headers: {
            'Authorization': `Bearer ${this.authToken}`
          }
        });
        
        if (response.ok) {
          // Try to get actual user info
          try {
            const userResponse = await fetch(`${this.registryUrl}/me`, {
              headers: {
                'Authorization': `Bearer ${this.authToken}`
              }
            });
            if (userResponse.ok) {
              this.currentUser = await userResponse.json();
            }
          } catch (e) {
            // If /me endpoint doesn't exist, extract from token or use placeholder
            this.currentUser = { username: 'User' };
          }
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
      // Load plugins
      const pluginsResponse = await fetch('/admin/plugin-manager/get-all-plugins');
      if (pluginsResponse.ok) {
        const pluginsData = await pluginsResponse.json();
        this.localPlugins = pluginsData.data || [];
      }

      const agentsResponse = await fetch('/agents/local');
      if (agentsResponse.ok) {
        const agentsData = await agentsResponse.json();
        this.localAgents = agentsData;
      }

      // Load agent ownership information
      const ownershipResponse = await fetch('/agents/ownership-info');
      if (ownershipResponse.ok) {
        this.agentOwnership = await ownershipResponse.json();
      }
    } catch (error) {
      console.error('Error loading local content:', error);
    }

    // Load top content by default
    if (this.searchResults.length === 0) {
      await this.loadTopContent();
    }
  }

  async handleLogin() {
    const username = this.shadowRoot.getElementById('username').value;
    const password = this.shadowRoot.getElementById('password').value;
    
    if (!username || !password) {
      this.showToast('Please enter username and password', 'error');
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
        
        // Get actual user info after login
        try {
          await this.checkAuthStatus();
        } catch (e) {
          // Fallback if checkAuthStatus fails
          this.currentUser = { username };
        }
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Login failed', 'error');
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
    }
    
    this.loading = false;
  }

  async handleRegister() {
    const username = this.shadowRoot.getElementById('reg-username').value;
    const email = this.shadowRoot.getElementById('reg-email').value;
    const password = this.shadowRoot.getElementById('reg-password').value;
    
    if (!username || !email || !password) {
      this.showToast('Please fill in all registration fields', 'error');
      return;
    }
    
    await this.register(username, email, password);
  }

  toggleRegisterForm() {
    this.showRegisterForm = !this.showRegisterForm;
  }

  logout() {
    this.authToken = null;
    this.isLoggedIn = false;
    this.currentUser = null;
    localStorage.removeItem('registry_token');
  }

  async loadTopContent() {
    this.loading = true;
    
    try {
      // Load top plugins and agents by default
      const response = await fetch(`${this.registryUrl}/search?limit=20&sort=downloads`);
      
      if (response.ok) {
        const data = await response.json();
        this.searchResults = data.results || [];
      } else {
        console.warn('Failed to load top content, trying basic search');
        // Fallback to empty search to get some results
        await this.search('', 'all');
      }
    } catch (error) {
      console.warn('Error loading top content:', error);
    }
    
    this.loading = false;
  }

  async search(query = this.searchQuery, category = this.selectedCategory) {
    this.loading = true;
    
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
        
        // Sort semantic results by distance (lower = better match)
        if (data.semantic_results) {
          data.semantic_results.sort((a, b) => (a.distance || 1) - (b.distance || 1));
        }
        
        // If we have semantic results, merge them with SQL results
        if (data.semantic_results && data.semantic_results.length > 0) {
          console.log('Merging semantic results:', data.semantic_results.length);
          
          // Create a map of existing results by ID
          const existingIds = new Set(this.searchResults.map(item => item.id.toString()));
          
          // Add semantic results that aren't already in SQL results
          const semanticItems = [];
          for (const semanticResult of data.semantic_results) {
            if (!existingIds.has(semanticResult.id)) {
              // Convert semantic result to content format
              const semanticItem = {
                id: parseInt(semanticResult.id),
                title: semanticResult.metadata.title || 'Unknown',
                description: semanticResult.document || '',
                category: semanticResult.metadata.category || 'unknown',
                distance_score: semanticResult.distance,
                is_semantic: true
              };
              semanticItems.push(semanticItem);
            }
          }
          // Sort semantic items by distance (best matches first - lower distance)
          semanticItems.sort((a, b) => (a.distance_score || 1) - (b.distance_score || 1));
          
          // Put best semantic matches at the top, then SQL results
          this.searchResults = [...semanticItems, ...this.searchResults];
        }
      } else {
        this.showToast('Search failed', 'error');
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
    }
    
    this.loading = false;
  }

  handleSearchInput(e) {
    this.searchQuery = e.target.value;
    
    // Clear existing timeout
    if (this.searchTimeout) {
      clearTimeout(this.searchTimeout);
    }
    
    // Set new timeout for auto-search after 500ms of no typing
    this.searchTimeout = setTimeout(() => {
      this.search();
    }, 500);
  }

  handleCategoryChange(category) {
    this.selectedCategory = category;
    this.search();
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
      this.showToast('Installation failed: ' + error.message, 'error');
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

  async installPersonaFromRegistry(personaRef, personaData, personaAssets) {
    try {
      const owner = personaRef.owner;
      const personaName = personaData.name;
      
      // Create the persona using the enhanced endpoint with asset support
      const response = await fetch('/personas/registry/with-assets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          persona: JSON.stringify(personaData),
          owner: owner,
          // Note: In a real implementation, we would need to download and upload
          // the actual asset files here. For now, we're just creating the persona
          // without assets, which will fall back to the original file-based approach.
        })
      });
      
      if (!response.ok) {
        console.warn('Failed to install persona via API, will be created during agent installation');
      }
      
      console.log(`Installed registry persona: registry/${owner}/${personaName}`);
    } catch (error) {
      console.error('Error installing persona from registry:', error);
      // Don't throw - let agent installation proceed, persona will be created then
    }
  }

  async installAgent(item) {
    // First, install persona if it has full persona data
    if (item.data.persona_data && item.data.persona_ref) {
      await this.installPersonaFromRegistry(item.data.persona_ref, item.data.persona_data, item.data.persona_assets);
    }
    
    const agentData = {
      // Start with the agent data from registry
      ...item.data,
      name: item.title,
      description: item.description,
      // Preserve ownership information from registry
      registry_owner: item.owner || item.creator,
      registry_id: item.id,
      registry_version: item.version,
      installed_from_registry: true,
      installed_at: new Date().toISOString()
    };
    
    // Handle enhanced persona data from registry
    if (item.data.persona_ref && item.data.persona_data) {
      // Use the registry persona reference
      const owner = item.data.persona_ref.owner;
      const personaName = item.data.persona_data.name;
      agentData.persona = `registry/${owner}/${personaName}`;
    } else {
      // Fallback to existing logic for backward compatibility
    
    // Handle persona field - if it's an object, ensure it has a name
    // If it's a string, leave it as is
    if (agentData.persona && typeof agentData.persona === 'object' && !agentData.persona.name) {
      // If persona is an object but doesn't have a name, use the agent name as persona name
      agentData.persona.name = agentData.name + '_persona';
    }
    
    // Handle registry persona installation with owner namespace
    if (agentData.persona && typeof agentData.persona === 'object') {
      // For registry installs, create namespaced persona reference
      const owner = item.owner || item.creator;
      if (owner) {
        agentData.persona = `registry/${owner}/${agentData.persona.name}`;
      }
    } else if (!agentData.persona) {
      // If no persona specified, use agent name
      agentData.persona = agentData.name;
    }
    }
    
    const response = await fetch('/agents/local', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: `agent=${encodeURIComponent(JSON.stringify(agentData))}`
    });
    
    if (!response.ok) {
      let errorMessage = `Agent installation failed: ${response.status}`;
      try {
        const errorData = await response.text();
        if (errorData) {
          errorMessage += ` - ${errorData}`;
        }
      } catch (e) {
        // If we can't read the error response, just use the status
      }
      throw new Error(errorMessage);
    }
  }

  async loadPersonaData(personaRef) {
    try {
      // Handle different persona reference formats
      let personaPath;
      if (personaRef.startsWith('registry/')) {
        // registry/owner/name format
        personaPath = `/personas/${personaRef}`;
      } else {
        // Simple name - check local first, then shared
        personaPath = `/personas/local/${personaRef}`;
      }
      
      const response = await fetch(personaPath);
      if (response.ok) {
        return await response.json();
      }
      
      // If local failed and not registry format, try shared
      if (!personaRef.startsWith('registry/')) {
        const sharedResponse = await fetch(`/personas/shared/${personaRef}`);
        if (sharedResponse.ok) {
          return await sharedResponse.json();
        }
      }
      
      return null;
    } catch (error) {
      console.error('Error loading persona data:', error);
      return null;
    }
  }

  async loadPersonaAssets(personaRef) {
    try {
      // For now, just return asset metadata - actual file upload would need backend support
      // In a full implementation, this would:
      // 1. Load the actual image files from the persona directory
      // 2. Calculate their hashes
      // 3. Check if they already exist in the asset store
      // 4. Upload them if needed
      // 5. Return the asset hashes for inclusion in the registry data
      
      // For Phase 3 implementation, we're focusing on the deduplication infrastructure
      // The actual asset upload during publishing would require:
      // - Reading image files from persona directories
      // - Converting them to base64 or FormData for upload
      // - Handling the upload to the registry backend
      // - Storing the returned asset hashes
      const assets = {};
      
      // Check if avatar exists by trying to load it
      const avatarPath = `/chat/personas/${personaRef}/avatar.png`;
      const avatarResponse = await fetch(avatarPath, { method: 'HEAD' });
      if (avatarResponse.ok) {
        assets.avatar = {
          path: avatarPath,
          exists: true
        };
      }
      
      return assets;
    } catch (error) {
      console.error('Error loading persona assets:', error);
      return {};
    }
  }

  _render() {
    return html`
      <div class="registry-manager">
        ${this.renderToasts()}
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
        ${this.showRegisterForm ? html`
          <div class="section">
            <h3>Create Account</h3>
            <div class="login-form">
              <input type="text" placeholder="Username" id="reg-username">
              <input type="email" placeholder="Email" id="reg-email">
              <input type="password" placeholder="Password" id="reg-password">
              <button class="primary" @click=${this.handleRegister} ?disabled=${this.loading}>
                ${this.loading ? 'Creating Account...' : 'Create Account'}
              </button>
              ${this.error ? html`<div class="error">${this.error}</div>` : ''}
            </div>
            <div class="auth-toggle">
              <button @click=${this.toggleRegisterForm}>Already have an account? Login</button>
            </div>
          </div>
        ` : html`
          <div class="section">
            <h3>Registry Login</h3>
            <div class="login-form">
              <input type="text" placeholder="Username or Email" id="username">
              <input type="password" placeholder="Password" id="password">
              <button class="primary" @click=${this.handleLogin} ?disabled=${this.loading}>
                ${this.loading ? 'Logging in...' : 'Login'}
              </button>
              ${this.error ? html`<div class="error">${this.error}</div>` : ''}
            </div>
            <div class="auth-toggle">
              <button @click=${this.toggleRegisterForm}>Don't have an account? Register</button>
            </div>
          </div>
        `}
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
        <div class="tab ${this.activeTab === 'settings' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'settings'}>Settings</div>
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
      case 'settings':
        return this.renderSettings();
      default:
        return this.renderSearch();
    }
  }

  renderSearch() {
    return html`
      <div class="section">
        <h3>Registry Browser</h3>
        <div class="search-form">
          <div class="form-row">
            <input type="text" placeholder="Search plugins and agents..." 
                   .value=${this.searchQuery}
                   @input=${this.handleSearchInput}>
          </div>
          <div class="category-tabs">
            <button class="category-tab ${this.selectedCategory === 'all' ? 'active' : ''}" 
                    @click=${() => this.handleCategoryChange('all')}>
              <span class="material-icons">apps</span>
              All
            </button>
            <button class="category-tab ${this.selectedCategory === 'plugin' ? 'active' : ''}" 
                    @click=${() => this.handleCategoryChange('plugin')}>
              <span class="material-icons">extension</span>
              Plugins
            </button>
            <button class="category-tab ${this.selectedCategory === 'agent' ? 'active' : ''}" 
                    @click=${() => this.handleCategoryChange('agent')}>
              <span class="material-icons">smart_toy</span>
              Agents
            </button>
          </div>
        </div>
        
        ${this.loading ? html`<div class="loading">Searching...</div>` : ''}
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        
        <div class="search-results">
          ${this.searchResults.length === 0 && !this.loading ? html`
            <div class="no-results">
              <p>No items found. Try adjusting your search terms or check your connection to the registry.</p>
              <button @click=${this.loadTopContent}>Load Popular Items</button>
            </div>
          ` : ''}
          ${this.searchResults.map(item => this.renderSearchResult(item))}
        </div>
      </div>
    `;
  }

  renderSearchResult(item) {
    return html`
      <div class="result-item">
        ${item.is_semantic ? html`
          <div class="semantic-badge">
            <span class="material-icons">psychology</span>
            Semantic Match ${item.distance_score ? `(${(1 - item.distance_score).toFixed(2)})` : ''}
          </div>
        ` : ''}
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
          ${this.isAgentInstalled(item.title) ? html`<button disabled>Installed</button>` : html`<button class="success" @click=${() => this.installFromRegistry(item)}>Install</button>`}
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
        <div class="form-row">
          <button @click=${this.refreshOwnershipCache} ?disabled=${this.loading}>
            Refresh Ownership Info
          </button>
          <span class="help-text">
            Last scanned: ${this.agentOwnership?.scanned_at ? 
              new Date(this.agentOwnership.scanned_at).toLocaleString() : 'Never'}
          </span>
        </div>
        <p>Select a local plugin or agent to publish to the registry:</p>
        
        ${this.loading ? html`<div class="loading">Publishing...</div>` : ''}
        ${this.publishSuccess ? html`<div class="success">${this.publishSuccess}</div>` : ''}
        ${this.error ? html`<div class="${this.error.includes('Successfully') ? 'success' : 'error'}">${this.error}</div>` : ''}
        
        <h4>Local Plugins (${this.localPlugins.length})</h4>
        ${this.localPlugins.length === 0 ? html`
          <p class="help-text">No local plugins found. Install some plugins first to publish them.</p>
        ` : html`
          ${this.localPlugins.map(plugin => html`
            <div class="result-item">
              <div class="result-header">
                <h5 class="result-title">${plugin.name}</h5>
                <span class="result-version">v${plugin.version || '1.0.0'}</span>
              </div>
              <p class="result-description">${plugin.description || 'No description available'}</p>
              <div class="result-meta">
                <span>Commands: ${plugin.commands?.length || 0}</span>
                <span>Services: ${plugin.services?.length || 0}</span>
              </div>
              <div class="result-actions">
                <button class="primary" @click=${() => this.publishItem(plugin, 'plugin')} ?disabled=${this.loading}>Publish Plugin</button>
              </div>
            </div>
          `)}
        `}
        
        <h4>Local Agents (${this.localAgents.length})</h4>
        ${this.localAgents.length === 0 ? html`
          <p class="help-text">No local agents found. Create some agents first to publish them.</p>
        ` : html`
          ${this.localAgents.map(agent => {
            // Check if this agent has external ownership
            const agentKey = `local/${agent.name}`;
            const ownershipInfo = this.agentOwnership?.agents?.[agentKey];
            const hasExternalOwner = ownershipInfo?.has_external_owner || false;
            const canPublish = !hasExternalOwner;
            const ownerName = ownershipInfo?.creator || ownershipInfo?.owner || ownershipInfo?.registry_owner || ownershipInfo?.created_by;
            
            return html`
            <div class="result-item">
              <h5 class="result-title">${agent.name}</h5>
              <p class="result-description">${agent.description || 'No description available'}</p>
              ${hasExternalOwner ? html`
                <p class="help-text" style="color: #dc3545;">Cannot publish: Agent created by ${ownerName || 'another user'}</p>
              ` : ''}
              <div class="result-actions">
                <button class="primary" 
                        @click=${() => this.publishItem(agent, 'agent')} 
                        ?disabled=${this.loading || !canPublish}>
                  Publish Agent
                </button>
              </div>
            </div>
            `;
          })}
        `}
      </div>
    `;
  }

  async refreshOwnershipCache() {
    this.loading = true;
    try {
      const response = await fetch('/agents/refresh-ownership-cache', {
        method: 'POST'
      });
      if (response.ok) {
        const result = await response.json();
        this.agentOwnership = result.data;
      }
    } catch (error) {
      console.error('Error refreshing ownership cache:', error);
    }
    this.loading = false;
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

  renderSettings() {
    return html`
      <div class="section">
        <h3>Registry Settings</h3>
        <div class="registry-url-display">
          Current registry: ${this.registryUrl}
        </div>
        <div class="form-row">
          <label>Registry URL:</label>
          <input type="url" 
                 placeholder="http://localhost:8000" 
                 .value=${this.registryUrl}
                 @input=${(e) => this.registryUrl = e.target.value}>
          <button @click=${() => this.updateRegistryUrl(this.registryUrl)}>Update</button>
          <button @click=${this.testConnection}>Test Connection</button>
        </div>
        ${this.error ? html`<div class="error">${this.error}</div>` : ''}
        <div class="help-text">
          Configure the MindRoot Registry URL. Default is http://localhost:8000
        </div>
      </div>
    `;
  }

  async publishItem(item, type) {
    if (!this.isLoggedIn) {
      this.error = 'Please log in to publish items';
      return;
    }

    this.loading = true;
    this.error = '';
    
    try {
      let publishData;
      
      if (type === 'plugin') {
        publishData = {
          title: item.name,
          description: item.description || `${item.name} plugin`,
          category: 'plugin',
          content_type: 'mindroot_plugin',
          version: item.version || '1.0.0',
          data: {
            plugin_info: item,
            installation: {
              type: item.source || 'pypi',
              source_path: item.source_path || item.name
            }
          },
          commands: item.commands || [],
          services: item.services || [],
          tags: item.tags || ['plugin'],
          dependencies: item.dependencies || [],
          github_url: item.github_url,
          pypi_module: item.pypi_module || item.name
        };
      } else if (type === 'agent') {
        // Load persona data if agent has a persona
        let personaData = null;
        let personaAssets = null;
        
        if (item.persona && typeof item.persona === 'string') {
          personaData = await this.loadPersonaData(item.persona);
          personaAssets = await this.loadPersonaAssets(item.persona);
        }
        
        publishData = {
          title: item.name,
          description: item.description || `${item.name} agent`,
          category: 'agent',
          content_type: 'mindroot_agent',
          version: item.version || '1.0.0',
          data: {
            agent_config: item,
            persona_ref: personaData ? {
              name: personaData.name,
              owner: this.currentUser?.username,
              version: personaData.version || '1.0.0',
              original_path: item.persona
            } : null,
            persona_data: personaData,
            persona_assets: personaAssets,
            // Keep original persona reference for backward compatibility
            persona: item.persona || {},
            instructions: item.instructions || '',
            model: item.model || 'default'
          },
          tags: item.tags || ['agent'],
          dependencies: item.dependencies || []
        };
      } else {
        throw new Error('Unknown item type');
      }
      
      const response = await fetch(`${this.registryUrl}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`
        },
        body: JSON.stringify(publishData)
      });
      
      if (response.ok) {
        const result = await response.json();
        this.showToast(`Successfully published ${publishData.title}!`, 'success');
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Publishing failed', 'error');
      }
    } catch (error) {
      this.showToast('Publishing failed: ' + error.message, 'error');
    }
    
    this.loading = false;
    this.requestUpdate();
  }

  showSuccessMessage(message) {
    // Create a temporary success state
    this.error = '';
    this.requestUpdate();
    
    // Clear success message after 5 seconds
    setTimeout(() => {
      this.publishSuccess = '';
      this.requestUpdate();
    }, 5000);
  }

  showErrorMessage(message) {
    this.error = message;
    this.publishSuccess = '';
    this.requestUpdate();
  }
}

customElements.define('registry-manager', RegistryManager);
