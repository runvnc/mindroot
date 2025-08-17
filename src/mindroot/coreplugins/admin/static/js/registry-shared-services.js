/**
 * Registry Shared Services
 * 
 * Contains all business logic, API calls, and utility functions
 * that are shared across different registry manager sections.
 */

class RegistrySharedServices {
  constructor(sharedState, mainComponent) {
    this.state = sharedState;
    this.main = mainComponent;
  }

  // === Authentication Services ===

  async checkAuthStatus() {
    if (this.state.authToken) {
      try {
        const response = await fetch(`${this.state.registryUrl}/stats`, {
          headers: {
            'Authorization': `Bearer ${this.state.authToken}`
          }
        });
        
        if (response.ok) {
          try {
            const userResponse = await fetch(`${this.state.registryUrl}/me`, {
              headers: {
                'Authorization': `Bearer ${this.state.authToken}`
              }
            });
            if (userResponse.ok) {
              this.state.currentUser = await userResponse.json();
            }
          } catch (e) {
            this.state.currentUser = { username: 'User' };
          }
          this.state.isLoggedIn = true;
        } else {
          this.logout();
        }
      } catch (error) {
        console.error('Error checking auth status:', error);
        this.logout();
      }
    }
  }

  async login(username, password) {
    this.state.loading = true;
    this.main.error = '';
    
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await fetch(`${this.state.registryUrl}/token`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        this.state.authToken = data.access_token;
        localStorage.setItem('registry_token', this.state.authToken);
        this.state.isLoggedIn = true;
        
        try {
          await this.checkAuthStatus();
        } catch (e) {
          this.state.currentUser = { username };
        }
        return true;
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Login failed', 'error');
        return false;
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
      return false;
    } finally {
      this.state.loading = false;
    }
  }

  async register(username, email, password) {
    this.state.loading = true;
    
    try {
      const response = await fetch(`${this.state.registryUrl}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password
        })
      });
      
      if (response.ok) {
        this.showToast('Registration successful! You can now log in.', 'success');
        return true;
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Registration failed', 'error');
        return false;
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
      return false;
    } finally {
      this.state.loading = false;
    }
  }

  logout() {
    this.state.authToken = null;
    this.state.isLoggedIn = false;
    this.state.currentUser = null;
    localStorage.removeItem('registry_token');
  }

  showToast(message, type = 'info', duration = 5000) {
    this.main.showToast(message, type, duration);
  }

  // === Data Loading Services ===

  async loadStats() {
    try {
      const response = await fetch(`${this.state.registryUrl}/stats`);
      if (response.ok) {
        this.main.stats = await response.json();
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
        this.state.localPlugins = pluginsData.data || [];
      }

      const agentsResponse = await fetch('/agents/local');
      if (agentsResponse.ok) {
        const agentsData = await agentsResponse.json();
        this.state.localAgents = agentsData;
      }

      const mcpResponse = await fetch('/admin/mcp/list');
      if (mcpResponse.ok) {
        const mcpData = await mcpResponse.json();
        this.main.localMcpServers = mcpData.data || [];
      }

      const ownershipResponse = await fetch('/agents/ownership-info');
      if (ownershipResponse.ok) {
        this.main.agentOwnership = await ownershipResponse.json();
      }
    } catch (error) {
      console.error('Error loading local content:', error);
    }

    if (this.main.searchResults.length === 0) {
      await this.loadTopContent();
    }
  }

  async loadTopContent() {
    this.state.loading = true;
    
    try {
      const response = await fetch(`${this.state.registryUrl}/search?limit=20&sort=downloads`);
      
      if (response.ok) {
        const data = await response.json();
        this.main.searchResults = data.results || [];
      } else {
        console.warn('Failed to load top content, trying basic search');
        await this.search('', 'all');
      }
    } catch (error) {
      console.warn('Error loading top content:', error);
    } finally {
      this.state.loading = false;
    }
  }

  // === Search Services ===

  async search(query = this.main.searchQuery, category = this.main.selectedCategory) {
    this.state.loading = true;
    
    try {
      const params = new URLSearchParams({
        query: query || '',
        limit: '20',
        semantic: 'true'
      });
      
      if (category && category !== 'all') {
        params.append('category', category);
      }
      
      const response = await fetch(`${this.state.registryUrl}/search?${params}`);
      
      if (response.ok) {
        const data = await response.json();
        this.main.searchResults = data.results || [];
        
        if (data.semantic_results && data.semantic_results.length > 0) {
          this.mergeSemanticResults(data.semantic_results);
        }
      } else {
        this.showToast('Search failed', 'error');
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
    } finally {
      this.state.loading = false;
    }
  }

  mergeSemanticResults(semanticResults) {
    semanticResults.sort((a, b) => (a.distance || 1) - (b.distance || 1));
    
    const existingIds = new Set(this.main.searchResults.map(item => item.id.toString()));
    const semanticItems = [];
    
    for (const semanticResult of semanticResults) {
      if (!existingIds.has(semanticResult.id)) {
        /*
        const semanticItem = {
          id: parseInt(semanticResult.id),
          title: semanticResult.metadata.title || 'Unknown',
          description: semanticResult.document || '',
          category: semanticResult.metadata.category || 'unknown',
          distance_score: semanticResult.distance,
          is_semantic: true
        }; */
        semanticItems.push(semanticResult);
      }
    }
    
    semanticItems.sort((a, b) => (a.distance_score || 1) - (b.distance_score || 1));
    this.main.searchResults = [...this.main.searchResults, ...semanticItems];
  }

  // === Installation Services ===

  async installFromRegistry(item) {
    this.state.loading = true;
    this.main.error = '';
    
    try {
      if (this.state.authToken) {
        await fetch(`${this.state.registryUrl}/install/${item.id}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.state.authToken}`
          }
        });
      }
      
      if (item.category === 'plugin') {
        await this.installPlugin(item);
      } else if (item.category === 'agent') {
        await this.installAgent(item);
        await this.checkAndInstallRecommendedPlugins(item);
      } else if (item.category === 'mcp_server') {
        await this.installMcpServer(item);
      }
      
      await this.loadLocalContent();
      this.state.loading = false;
      this.showToast('Item installed successfully!', 'success');
      
      await new Promise(resolve => setTimeout(resolve, 100));
      
    } catch (error) {
      this.state.loading = false;
      this.showToast('Installation failed: ' + error.message, 'error');
    }
  }

  async installMcpServer(item) {
    // Retrieve secrets from the main component's state
    const secrets = this.main.mcpInstallSecrets[item.id] || null;
    console.log(`[SharedServices] Installing MCP Server '${item.title}' (ID: ${item.id}) with secrets:`, secrets ? Object.keys(secrets) : 'None');

    try {
      if (item.data && item.data.auth_type === 'oauth2') {
        await this.installOAuthMcpServer(item);
      } else {
        // Use the new install endpoint that accepts secrets
        const response = await fetch('/admin/mcp/install', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            registry_id: item.id,
            registry_url: this.state.registryUrl,
            secrets: secrets
          })
        });
        
        if (response.ok) {
          this.showToast(`MCP Server '${item.title}' installed successfully.`, 'success');
        } else {
          const err = await response.json();
          throw new Error(err.detail || 'Failed to install MCP server');
        }
      }
    } catch (error) {
      throw new Error(`MCP Server installation failed: ${error.message}`);
    }
  }

  /**
   * Connect an already installed OAuth MCP server from a registry item.
   * This triggers the /admin/mcp/test-remote -> OAuth popup -> /complete-oauth flow,
   * then refreshes local MCP list and attempts a final /admin/mcp/connect to ensure
   * dynamic MCP commands are registered.
   */
  async connectInstalledOAuthMcp(item) {
    try {
      // Derive name and URL from registry data and local list
      const serverName = item.data?.name || item.title;
      const remoteUrl = item.data?.transport_url || item.data?.url || item.data?.provider_url || item.data?.authorization_server_url || '';

      if (!serverName) {
        throw new Error('Missing server name');
      }
      if (!remoteUrl) {
        // Fallback: try to infer from local list
        const localServer = (this.main.localMcpServers || []).find(s => s.name === item.title || s.name === serverName);
        if (localServer?.transport_url) {
          // ok
        } else {
          this.showToast('Cannot determine remote URL for OAuth connection', 'error');
          return false;
        }
      }

      // Kick off test-remote to either connect or return requires_oauth
      const testResp = await fetch('/admin/mcp/test-remote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: remoteUrl, name: serverName })
      });
      const testData = await testResp.json();

      if (testData.success) {
        this.showToast(testData.message || `Connected to '${serverName}'.`, 'success');
        await this.loadLocalContent();
        return true;
      }

      if (testData.requires_oauth && testData.auth_url && testData.server_name) {
        await this.startOAuthWindowFlow({
          server_name: testData.server_name,
          auth_url: testData.auth_url,
          remote_url: remoteUrl
        });
        // startOAuthWindowFlow does post-completion recheck and refresh
        return true;
      }

      throw new Error(testData.detail || 'Connection failed');
    } catch (e) {
      this.showToast(`Connect failed: ${e.message}`, 'error');
      return false;
    }
  }

  async installOAuthMcpServer(item) {
    try {
      // 1) Ensure the server exists in backend manager
      const addResp = await fetch('/admin/mcp/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item.data)
      });
      if (!addResp.ok) {
        const err = await addResp.json();
        throw new Error(err.detail || 'Failed to install MCP server');
      }
      this.showToast(`MCP Server '${item.title}' installed locally. Connecting...`, 'info');

      // 2) Kick off connection test which will return requires_oauth if needed
      const testBody = {
        url: item.data.transport_url || item.data.url || item.data.provider_url || item.data.authorization_server_url || '',
        name: item.data.name || item.title
      };
      const testResp = await fetch('/admin/mcp/test-remote', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testBody)
      });
      const testData = await testResp.json();

      if (testData.success) {
        this.showToast(testData.message || `Connected to '${item.title}'.`, 'success');
        return true;
      }

      if (testData.requires_oauth && testData.auth_url && testData.server_name) {
        // 3) Open OAuth window and wire completion to /admin/mcp/complete-oauth
        await this.startOAuthWindowFlow({
          server_name: testData.server_name,
          auth_url: testData.auth_url,
          remote_url: testBody.url
        });
        return true;
      }

      throw new Error(testData.detail || 'Connection failed');
    } catch (error) {
      throw new Error(`OAuth MCP Server installation failed: ${error.message}`);
    }
  }

  async startOAuthWindowFlow({ server_name, auth_url, remote_url }) {
    this.showToast(`Opening OAuth authorization for '${server_name}'...`, 'info');

    const width = 600;
    const height = 700;
    const left = (screen.width - width) / 2;
    const top = (screen.height - height) / 2;
    const popup = window.open(
      auth_url,
      'oauth_window',
      `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
    );

    if (!popup) {
      this.showToast('Failed to open OAuth window. Please allow popups and try again.', 'error');
      return false;
    }

    const onMessage = async (event) => {
      if (!event.data || event.data.type !== 'oauth_callback') return;
      window.removeEventListener('message', onMessage);
      try {
        // Close popup ASAP
        if (popup && !popup.closed) popup.close();

        // Complete the OAuth flow with backend
        const resp = await fetch('/admin/mcp/complete-oauth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ server_name, code: event.data.code, state: event.data.state })
        });
        const data = await resp.json();

        if (!data.success) {
          this.showToast(data.detail || 'OAuth completion failed', 'error');
          return false;
        }

        // Optionally re-test to fetch tools, like publisher
        try {
          const recheck = await fetch('/admin/mcp/test-remote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: remote_url, name: server_name })
          });
          const reData = await recheck.json();
          if (reData.success) {
            this.showToast(reData.message || `Connected to '${server_name}'.`, 'success');
          }
        } catch (e) {
          // ignore
        }

        // Ensure dynamic commands are ready by refreshing local content
        await this.loadLocalContent();

        // As a final safety, if not connected, try /admin/mcp/connect
        try {
          await fetch('/admin/mcp/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ server_name })
          });
          await this.loadLocalContent();
        } catch (_) {}

        return true;
      } catch (err) {
        this.showToast(`OAuth completion failed: ${err.message}`, 'error');
        return false;
      }
    };

    window.addEventListener('message', onMessage);

    // Cleanup if user closes popup before finishing
    const checkClosed = setInterval(() => {
      if (!popup || popup.closed) {
        clearInterval(checkClosed);
        window.removeEventListener('message', onMessage);
      }
    }, 1000);
  }

  async installPlugin(item) {
    return new Promise((resolve, reject) => {
      try {
        let installDialog = document.querySelector('plugin-install-dialog');
        if (!installDialog) {
          installDialog = document.createElement('plugin-install-dialog');
          document.body.appendChild(installDialog);
        }

        const source = item.github_url ? 'github' : 'pypi';
        const sourcePath = item.github_url || item.pypi_module;

        installDialog.open(item.title, source.charAt(0).toUpperCase() + source.slice(1));

        const params = new URLSearchParams();
        params.append('plugin', item.title);
        params.append('source', source);
        params.append('source_path', sourcePath);

        const eventSource = new EventSource(`/plugin-manager/stream-install-plugin?${params.toString()}`);
        let hasError = false;

        eventSource.addEventListener('message', (event) => {
          installDialog.addOutput(event.data, 'info');
        });

        eventSource.addEventListener('error', (event) => {
          hasError = true;
          installDialog.addOutput(event.data, 'error');
        });

        eventSource.addEventListener('warning', (event) => {
          installDialog.addOutput(event.data, 'warning');
        });

        eventSource.addEventListener('complete', (event) => {
          installDialog.addOutput(event.data, 'success');
          installDialog.setComplete(hasError);
          eventSource.close();
          this.loadLocalContent(); // Refresh plugin list
          resolve();
        });

        eventSource.onerror = (err) => {
          if (eventSource.readyState === EventSource.CLOSED) {
            if (!hasError) {
              installDialog.setComplete(false); // Closed cleanly
            } else {
              installDialog.addOutput('Connection closed with an error.', 'error');
              installDialog.setComplete(true);
            }
          } else {
            installDialog.addOutput('An unknown error occurred with the connection.', 'error');
            installDialog.setComplete(true);
          }
          eventSource.close();
          reject(new Error('Plugin installation stream failed.'));
        };
      } catch (error) {
        this.showToast(`Failed to start plugin installation: ${error.message}`, 'error');
        reject(error);
      }
    });
  }

  async installAgent(item) {
    console.log('Installing agent from registry:', item);
    
    if (item.data.persona_data && item.data.persona_ref) {
      const personaAssets = await this.extractPersonaAssets(item.data.persona_ref, item.data.persona_data);
      await this.installPersonaFromRegistry(item.data.persona_ref, item.data.persona_data, personaAssets);
    }
    
    const agentData = this.buildAgentData(item);
    
    const response = await fetch('/agents/local', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: `agent=${encodeURIComponent(JSON.stringify(agentData))}`
    });
    
    if (!response.ok) {
      const errorData = await response.text();
      if (errorData.includes('already exists')) {
        const confirmOverwrite = confirm(`Agent "${agentData.name}" already exists. Do you want to overwrite it?`);
        if (confirmOverwrite) {
          agentData.overwrite = true;
          const retryResponse = await fetch('/agents/local', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `agent=${encodeURIComponent(JSON.stringify(agentData))}`
          });
          
          if (!retryResponse.ok) {
            throw new Error(`Agent installation failed: ${retryResponse.status}`);
          }
        } else {
          throw new Error('Installation cancelled by user');
        }
      } else {
        throw new Error(`Agent installation failed: ${response.status} - ${errorData}`);
      }
    }
  }

  buildAgentData(item) {
    const agentData = {
      ...item.data.agent_config || {},
      name: item.title,
      description: item.description,
      instructions: item.data.instructions || item.data.agent_config?.instructions || '',
      model: item.data.model || item.data.agent_config?.model || 'default',
      recommended_plugins: item.data.recommended_plugins || item.data.required_plugins || item.data.agent_config?.recommended_plugins || item.data.agent_config?.required_plugins || [],
      registry_owner: item.owner || item.creator,
      registry_id: item.id,
      registry_version: item.version,
      installed_from_registry: true,
      installed_at: new Date().toISOString()
    };

    if (item.data.persona_ref && item.data.persona_data) {
      const owner = item.data.persona_ref.owner;
      const personaName = item.data.persona_data.name;
      agentData.persona = `registry/${owner}/${personaName}`;
    } else if (!agentData.persona) {
      agentData.persona = agentData.name;
    }

    return agentData;
  }

  async extractPersonaAssets(personaRef, personaData) {
    try {
      const assets = {};
      const personaAssets = personaData.persona_assets || {};
      
      if (personaAssets.avatar) {
        const base64Data = personaAssets.avatar.data;
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: personaAssets.avatar.type || 'image/png' });
        assets.avatar = blob;
      } else if (personaData.asset_hashes?.avatar) {
        try {
          const response = await fetch(`${this.state.registryUrl}/assets/${personaData.asset_hashes.avatar}`);
          if (response.ok) {
            assets.avatar = await response.blob();
          }
        } catch (e) {
          console.log('Could not download avatar from asset store:', e);
        }
      }
      
      if (personaAssets.faceref) {
        const base64Data = personaAssets.faceref.data;
        const binaryString = atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: personaAssets.faceref.type || 'image/png' });
        assets.faceref = blob;
      } else if (personaData.asset_hashes?.faceref) {
        try {
          const response = await fetch(`${this.state.registryUrl}/assets/${personaData.asset_hashes.faceref}`);
          if (response.ok) {
            assets.faceref = await response.blob();
          }
        } catch (e) {
          console.log('Could not download faceref from asset store:', e);
        }
      }
      
      return assets;
    } catch (error) {
      console.error('Error extracting persona assets:', error);
      return {};
    }
  }

  async installPersonaFromRegistry(personaRef, personaData, personaAssets) {
    try {
      const owner = personaRef.owner;
      const personaName = personaData.name;
      
      const cleanPersonaData = {
        name: personaData.name,
        description: personaData.description,
        instructions: personaData.instructions,
        model: personaData.model,
        version: personaData.version,
        moderated: personaData.moderated
      };
      
      Object.keys(cleanPersonaData).forEach(key => {
        if (cleanPersonaData[key] === undefined) {
          delete cleanPersonaData[key];
        }
      });
      
      const formData = new FormData();
      formData.append('persona', JSON.stringify(cleanPersonaData));
      formData.append('owner', owner);
      
      if (personaAssets && personaAssets.avatar) {
        formData.append('avatar', personaAssets.avatar, 'avatar.png');
      }
      
      if (personaAssets && personaAssets.faceref) {
        formData.append('faceref', personaAssets.faceref, 'faceref.png');
      }
      
      const response = await fetch('/personas/registry/with-assets', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      console.log(`Installed registry persona: registry/${owner}/${personaName}`);
    } catch (error) {
      console.error('Error installing persona from registry:', error);
      throw error;
    }
  }

  async checkAndInstallRecommendedPlugins(item) {
    try {
      const agentName = item.title;
      const checkResponse = await fetch(`/admin/check-recommended-plugins/${encodeURIComponent(agentName)}`);
      
      if (checkResponse.ok) {
        const checkData = await checkResponse.json();
        
        if (checkData.pending_plugins && checkData.pending_plugins.length > 0) {
          console.log(`Found ${checkData.pending_plugins.length} recommended plugins to install:`, checkData.pending_plugins);
          
          this.showToast(`Installing ${checkData.pending_plugins.length} recommended plugins...`, 'info');
          
          let installDialog = document.querySelector('plugin-install-dialog');
          if (!installDialog) {
            installDialog = document.createElement('plugin-install-dialog');
            document.body.appendChild(installDialog);
          }
          
          installDialog.open(`Recommended plugins for ${agentName}`, 'Agent Setup');
          
          const eventSource = new EventSource(`/admin/stream-install-recommended-plugins/${encodeURIComponent(agentName)}`);
          
          let hasError = false;
          let receivedEnd = false;
          
          eventSource.onmessage = (event) => {
            if (event.data === 'END') {
              receivedEnd = true;
              eventSource.close();
              installDialog.setComplete(hasError);
              this.loadLocalContent();
            } else {
              if (event.data.startsWith('ERROR:')) {
                hasError = true;
                installDialog.addOutput(event.data, 'error');
              } else if (event.data.startsWith('WARNING:')) {
                installDialog.addOutput(event.data, 'warning');
              } else {
                installDialog.addOutput(event.data, 'info');
              }
            }
          };
          
          eventSource.onerror = () => {
            if (!receivedEnd) {
              if (eventSource.readyState === EventSource.CLOSED) {
                hasError = true;
                installDialog.addOutput('Connection closed unexpectedly', 'error');
                installDialog.setComplete(true);
              }
            }
            eventSource.close();
          };
        } else {
          const agentRecommended = item.data.recommended_plugins || item.data.required_plugins || [];
          if (agentRecommended.length > 0) {
            this.showToast(`All ${agentRecommended.length} recommended plugins are already installed`, 'success');
          }
        }
      }
    } catch (error) {
      console.error('Error checking recommended plugins:', error);
    }
  }
  // === Publishing Services ===

  async refreshOwnershipCache() {
    this.state.loading = true;
    try {
      const response = await fetch('/agents/refresh-ownership-cache', {
        method: 'POST'
      });
      if (response.ok) {
        const result = await response.json();
        this.main.agentOwnership = result.data;
      }
    } catch (error) {
      console.error('Error refreshing ownership cache:', error);
    } finally {
      this.state.loading = false;
    }
  }

  async publishPluginFromGithub(repo) {
    if (!repo || !repo.includes('/')) {
      this.showToast('Please provide a valid GitHub repository (e.g., user/repo)', 'error');
      return false;
    }

    this.state.loading = true;
    this.main.error = '';

    try {
      const response = await fetch('/admin/plugins/publish_from_github', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.state.authToken}`
        },
        body: JSON.stringify({ repo: repo, registry_url: this.state.registryUrl })
      });

      if (response.ok) {
        const result = await response.json();
        this.showToast(result.message || 'Published successfully!', 'success');
        return true;
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Publishing failed', 'error');
        return false;
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
      return false;
    } finally {
      this.state.loading = false;
    }
  }

  // === Settings Services ===

  async updateRegistryUrl(newUrl) {
    this.state.registryUrl = newUrl;
    localStorage.setItem('registry_url', newUrl);
    this.logout();
    await this.loadStats();
    this.main.requestUpdate();
  }

  async testConnection() {
    try {
      const response = await fetch(`${this.state.registryUrl}/stats`);
      if (response.ok) {
        this.main.error = '';
        await this.loadStats();
        const originalError = this.main.error;
        this.main.error = 'Connection successful!';
        this.main.requestUpdate();
        setTimeout(() => {
          this.main.error = originalError;
          this.main.requestUpdate();
        }, 2000);
      } else {
        this.main.error = `Connection failed: ${response.status}`;
      }
    } catch (error) {
      this.main.error = `Connection failed: ${error.message}`;
    }
    this.main.requestUpdate();
  }
}

export { RegistrySharedServices };
