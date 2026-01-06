import { BaseEl } from '/admin/static/js/base.js';
import { html, css } from '/admin/static/js/lit-core.min.js';

class McpPublisher extends BaseEl {
  static properties = {
    serverType: { type: String },
    serverName: { type: String },
    serverDescription: { type: String },
    localConfig: { type: Object },
    remoteUrl: { type: String },
    authType: { type: String },
    discoveredTools: { type: Array },
    loading: { type: Boolean },
    error: { type: String },
    success: { type: String },
    oauthFlow: { type: Object },
    oauthWindow: { type: Object },
    registryUrl: { type: String },
    authToken: { type: String },
    isLoggedIn: { type: Boolean },
    requiredPlaceholders: { type: Array },
    placeholderValues: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .mcp-publisher {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-width: 800px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }

    .form-row {
      display: flex;
      gap: 1rem;
      align-items: center;
    }

    label {
      color: #fff;
      font-weight: 500;
    }

    input, textarea, select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      font-family: inherit;
    }

    input:focus, textarea:focus, select:focus {
      outline: none;
      border-color: #4a9eff;
    }

    textarea {
      min-height: 100px;
      font-family: 'Courier New', monospace;
      resize: vertical;
    }

    .checkbox-group {
      display: flex;
      gap: 1rem;
      margin: 1rem 0;
    }

    .checkbox-item {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
    }

    input[type="checkbox"] {
      width: auto;
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

    .tools-preview {
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      padding: 1rem;
      margin-top: 1rem;
    }

    .tool-item {
      background: rgba(255, 255, 255, 0.05);
      padding: 0.5rem;
      border-radius: 4px;
      margin-bottom: 0.5rem;
    }

    .tool-name {
      font-weight: bold;
      color: #4a9eff;
    }

    .tool-description {
      color: #ccc;
      font-size: 0.9rem;
      margin-top: 0.25rem;
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

    .loading {
      text-align: center;
      color: #ccc;
      padding: 1rem;
    }

    .help-text {
      font-size: 0.8rem;
      color: #999;
      margin-top: 0.25rem;
    }

    .json-example {
      background: rgba(0, 0, 0, 0.3);
      padding: 0.5rem;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 0.8rem;
      color: #ccc;
      white-space: pre-wrap;
      margin-top: 0.5rem;
    }

    .oauth-status {
      background: rgba(74, 158, 255, 0.2);
      color: #4a9eff;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }
  `;

  constructor() {
    super();
    this.serverType = 'local';
    this.serverName = '';
    this.serverDescription = '';
    this.localConfig = {
      command: '',
      args: [],
      env: {}
    };
    this.remoteUrl = '';
    this.authType = 'none';
    this.discoveredTools = [];
    this.loading = false;
    this.error = '';
    this.success = '';
    this.oauthFlow = null;
    this.oauthWindow = null;
    this.registryUrl = '';
    this.authToken = '';
    this.isLoggedIn = false;
    this.requiredPlaceholders = [];
    this.placeholderValues = {};
    
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

  handleServerTypeChange(e) {
    this.serverType = e.target.value;
    this.discoveredTools = [];
    this.error = '';
    this.oauthFlow = null;
  }

  handleLocalConfigChange(e) {
    try {
      const config = JSON.parse(e.target.value);
      this.localConfig = {
        command: config.command || '',
        args: config.args || [],
        env: config.env || {}
      };
      this.scanForRequiredSecrets();
      this.error = '';
    } catch (error) {
      this.error = 'Invalid JSON configuration';
    }
  }

  scanForRequiredSecrets() {
    const placeholders = new Set();

    // 1. Add all keys from the 'env' object automatically.
    if (this.localConfig.env) {
      Object.keys(this.localConfig.env).forEach(key => placeholders.add(key));
    }

    // 2. Scan the entire configuration for <PLACEHOLDER> syntax.
    const configString = JSON.stringify(this.localConfig);
    const placeholderRegex = /<([A-Z0-9_]+)>/g;
    let match;
    while ((match = placeholderRegex.exec(configString)) !== null) {
      placeholders.add(match[1]);
    }

    this.requiredPlaceholders = Array.from(placeholders);
    // Reset values for placeholders that no longer exist
    const newValues = {};
    this.requiredPlaceholders.forEach(p => {
      if (this.placeholderValues[p]) {
        newValues[p] = this.placeholderValues[p];
      }
    });
    this.placeholderValues = newValues;
  }

  async discoverTools() {
    if (!this.serverName.trim()) {
      this.error = 'Please enter a server name first';
      return;
    }

    this.loading = true;
    this.error = '';
    this.success = '';
    this.discoveredTools = [];
    this.oauthFlow = null;

    try {
      if (this.serverType === 'local') {
        await this.discoverLocalTools();
      } else {
        await this.discoverRemoteTools();
      }
    } catch (error) {
      this.error = `Failed to discover tools: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async discoverLocalTools() {
    if (!this.localConfig.command) {
      throw new Error('Command is required for local servers');
    }

    // Use the new dedicated endpoint for testing local servers
    const response = await fetch('/admin/mcp/test-local', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: this.serverName,
        command: this.localConfig.command,
        args: this.localConfig.args,
        env: this.localConfig.env,
        secrets: this.placeholderValues
      })
    });

    const data = await response.json();
    if (data.success) {
      this.discoveredTools = data.tools || [];
      this.success = data.message;
    } else {
      throw new Error(data.detail || 'Local server test failed');
    }
  }

  async discoverRemoteTools() {
    if (!this.remoteUrl) {
      throw new Error('URL is required for remote servers');
    }

    // Use the new backend endpoint that handles OAuth
    console.log('[MCP-Publisher] discoverRemoteTools: starting test-remote', { url: this.remoteUrl, name: this.serverName });
    const response = await fetch('/admin/mcp/test-remote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: this.remoteUrl,
        name: this.serverName
      })
    });

    const data = await response.json();
    console.log('[MCP-Publisher] discoverRemoteTools: response', data);

    if (data.success) {
      // Successfully connected without OAuth
      this.discoveredTools = data.tools || [];
      console.log('[MCP-Publisher] discoverRemoteTools: tools discovered (no OAuth)', this.discoveredTools);
      this.success = data.message;
      // Default remote auth type to 'auto' unless specified
      this.authType = 'auto';
    } else if (data.requires_oauth) {
      // OAuth flow required
      this.oauthFlow = {
        auth_url: data.auth_url,
        flow_id: data.flow_id,
        server_name: data.server_name
      };
      // Ensure we publish with remote auth type when OAuth was needed
      this.authType = 'oauth2';
      this.success = data.message;
      console.log('[MCP-Publisher] discoverRemoteTools: OAuth required', this.oauthFlow);
      
      // Automatically open OAuth window
      await this.startOAuthFlow();
    } else {
      // Other error
      throw new Error(data.detail || 'Connection failed');
    }
  }

  async startOAuthFlow() {
    if (!this.oauthFlow || !this.oauthFlow.auth_url) {
      this.error = 'No OAuth flow available';
      return;
    }

    this.success = 'Opening OAuth authorization window...';
    console.log('[MCP-Publisher] startOAuthFlow: opening', this.oauthFlow?.auth_url);
    
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
      // Polling for window status; discoveredTools length:', this.discoveredTools?.length
      console.log('[MCP-Publisher] startOAuthFlow: polling window closed?', this.oauthWindow?.closed, 'tools:', this.discoveredTools?.length);
      if (this.oauthWindow && this.oauthWindow.closed) {
        clearInterval(checkClosed);
        if (!this.discoveredTools.length) {
          this.error = 'OAuth window was closed before completion';
          this.loading = false;
        }
      } else {
        if (!this.oauthWindow && this.discoveredTools.length) {
          clearInterval(checkClosed);
          this.success = 'OAuth flow completed successfully, tools discovered.';
          this.loading = false;
        }
      }
    }, 1000);
  }

  async handleOAuthCallback(event) {
    // Only handle messages from our OAuth window
    if (!this.oauthWindow || event.source !== this.oauthWindow) {
      // Note: admin UI can receive unrelated messages; ignore safely
      // console.debug('[MCP-Publisher] handleOAuthCallback: ignoring message from different source');
      return;
    }

    if (event.data && event.data.type === 'oauth_callback' && event.data.code) {
      try {
        this.success = 'OAuth authorization received, completing flow...';
        console.log('[MCP-Publisher] handleOAuthCallback: received code/state', { code: !!event.data.code, state: event.data.state });
        
        // Close the OAuth window
        this.oauthWindow.close();
        this.oauthWindow = null;

        // Complete the OAuth flow
        const response = await fetch('/admin/mcp/complete-oauth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            server_name: this.oauthFlow.server_name,
            code: event.data.code,
            state: event.data.state
          })
        });

        const data = await response.json();
        console.log('[MCP-Publisher] handleOAuthCallback: complete-oauth response', data);

        if (data.success) {
          // Prefer tools from response; if pending, poll once for updated status
          if (Array.isArray(data.tools) && data.tools.length) {
            this.discoveredTools = data.tools;
            console.log('[MCP-Publisher] handleOAuthCallback: tools from complete-oauth', this.discoveredTools);
          } else {
            // Fallback: ask backend for oauth-status and try to extract tools if connected
            try {
              const statusResp = await fetch(`/admin/mcp/oauth-status/${this.oauthFlow.server_name}`);
              if (statusResp.ok) {
                const statusData = await statusResp.json();
                console.log('[MCP-Publisher] handleOAuthCallback: oauth-status', statusData);
                // If server appears connected, re-trigger a lightweight test to fetch tools
                if (statusData && statusData.status === 'connected') {
                  const recheck = await fetch('/admin/mcp/test-remote', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: this.remoteUrl, name: this.oauthFlow.server_name })
                  });
                  const reData = await recheck.json();
                  console.log('[MCP-Publisher] handleOAuthCallback: recheck test-remote response', reData);
                  if (reData.success && Array.isArray(reData.tools)) {
                    this.discoveredTools = reData.tools;
                  }
                }
                // If still pending, start a short polling loop for connection then fetch tools
                if (!this.discoveredTools.length) {
                  await this.pollForToolsAfterOAuth(6);
                }
              }
            } catch (e) {
              console.warn('Post-OAuth tool recheck failed', e);
            }
          }
          this.success = data.message;
          this.oauthFlow = null;
        } else {
          throw new Error(data.detail || 'OAuth completion failed');
        }
      } catch (error) {
        this.error = `OAuth completion failed: ${error.message}`;
        this.oauthFlow = null;
      } finally {
        this.loading = false;
      }
    }
  }

  async pollForToolsAfterOAuth(maxTries = 6, delayMs = 1000) {
    console.log('[MCP-Publisher] pollForToolsAfterOAuth: start', { maxTries, delayMs, server: this.oauthFlow?.server_name });
    for (let i = 0; i < maxTries && (!this.discoveredTools || this.discoveredTools.length === 0); i++) {
      try {
        const statusResp = await fetch(`/admin/mcp/oauth-status/${this.oauthFlow.server_name}`);
        const status = statusResp.ok ? await statusResp.json() : null;
        console.log(`[MCP-Publisher] pollForToolsAfterOAuth: try ${i+1} status`, status);
        if (status && status.status === 'connected') {
          const recheck = await fetch('/admin/mcp/test-remote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: this.remoteUrl, name: this.oauthFlow.server_name })
          });
          const reData = await recheck.json();
          console.log('[MCP-Publisher] pollForToolsAfterOAuth: test-remote response', reData);
          if (reData.success && Array.isArray(reData.tools) && reData.tools.length) {
            this.discoveredTools = reData.tools;
            console.log('[MCP-Publisher] pollForToolsAfterOAuth: tools discovered', this.discoveredTools);
            return true;
          }
        }
      } catch (e) {
        console.warn('[MCP-Publisher] pollForToolsAfterOAuth: error', e);
      }
      await new Promise(res => setTimeout(res, delayMs));
    }
    console.log('[MCP-Publisher] pollForToolsAfterOAuth: end, tools found?', this.discoveredTools?.length);
    return false;
  }

  async publishServer() {
    if (!this.serverName.trim()) {
      this.error = "Server name is required";
      return;
    }

    if (!this.serverDescription.trim()) {
      this.error = "Server description is required";
      return;
    }

    if (this.discoveredTools.length === 0) {
      this.error = "Please discover tools first";
      return;
    }

    if (!this.isLoggedIn || !this.authToken) {
      this.error = "Please log in to the registry first (top of page).";
      return;
    }

    if (!this.registryUrl) {
      this.error = "Registry URL is not configured.";
      return;
    }

    this.loading = true;
    this.error = "";
    this.success = "";

    try {
      // Prepare server configuration based on type
      const serverData = {
        name: this.serverName,
        description: this.serverDescription,
        server_type: this.serverType,
        tools: this.discoveredTools,
        transport: this.serverType === 'local' ? 'stdio' : 'http',
        auth_type: this.serverType === 'local' ? 'none' : this.authType
      };
      
      // Add type-specific configuration
      if (this.serverType === "local") {
        Object.assign(serverData, {
          command: this.localConfig.command,
          args: this.localConfig.args,
          env: this.localConfig.env
        });
      } else {
        Object.assign(serverData, {
          url: this.remoteUrl
        });
      }

      // Build registry publish payload (align with registry ContentCreate)
      const publishData = {
        title: this.serverName,
        description: this.serverDescription,
        category: "mcp_server",
        content_type: "mcp_server",
        version: "1.0.0",
        data: serverData,
        tags: ["mcp", "server", this.serverType],
        dependencies: []
      };

      const response = await fetch(`${this.registryUrl}/publish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${this.authToken}`
        },
        body: JSON.stringify(publishData)
      });

      if (response.ok) {
        const result = await response.json();
        this.success = result.message || `MCP Server "${this.serverName}" published successfully!`;
        this.resetForm();
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Publishing failed");
      }
    } catch (error) {
      this.error = `Publishing failed: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  resetForm() {
    this.serverName = '';
    this.serverDescription = '';
    this.localConfig = { command: '', args: [], env: {} };
    this.remoteUrl = '';
    this.discoveredTools = [];
    this.oauthFlow = null;
  }

  _render() {
    return html`
      <div class="mcp-publisher">
        <div class="section">
          <h3>Publish MCP Server</h3>
          
          ${this.error ? html`<div class="error">${this.error}</div>` : ''}
          ${this.success ? html`<div class="success">${this.success}</div>` : ''}
          ${this.oauthFlow ? html`<div class="oauth-status">OAuth flow in progress...</div>` : ''}
          
          <div class="form-group">
            <label>Server Name</label>
            <input type="text" 
                   .value=${this.serverName}
                   @input=${(e) => this.serverName = e.target.value}
                   placeholder="my-awesome-server">
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea .value=${this.serverDescription}
                     @input=${(e) => this.serverDescription = e.target.value}
                     placeholder="Describe what this MCP server does..."></textarea>
          </div>

          <div class="form-group">
            <label>Server Type</label>
            <div class="checkbox-group">
              <div class="checkbox-item">
                <input type="radio" 
                       name="serverType" 
                       value="local" 
                       .checked=${this.serverType === 'local'}
                       @change=${this.handleServerTypeChange}>
                <label>Local (stdio)</label>
              </div>
              <div class="checkbox-item">
                <input type="radio" 
                       name="serverType" 
                       value="remote" 
                       .checked=${this.serverType === 'remote'}
                       @change=${this.handleServerTypeChange}>
                <label>Remote (HTTP/SSE)</label>
              </div>
            </div>
          </div>

          ${this.serverType === 'local' ? this.renderLocalConfig() : this.renderRemoteConfig()}
          ${this.serverType === 'local' && this.requiredPlaceholders.length > 0 ? this.renderPlaceholderInputs() : ''}

          <div class="form-row">
            <button @click=${this.discoverTools} ?disabled=${this.loading} class="primary">
              ${this.loading ? 'Discovering...' : 'Discover & Connect'}
            </button>
          </div>

          ${this.discoveredTools.length > 0 ? this.renderToolsPreview() : ''}
        </div>
      </div>
    `;
  }

  renderLocalConfig() {
    const exampleConfig = {
      command: "npx",
      args: ["-y", "slack-mcp-server@latest"],
      env: {
        "SLACK_MCP_XOXP_TOKEN": "xoxp-YOUR-TOKEN-HERE"
      }
    };

    return html`
      <div class="form-group">
        <label>Local Server Configuration (JSON)</label>
        <textarea @input=${this.handleLocalConfigChange} placeholder="Enter JSON configuration...">${JSON.stringify(this.localConfig, null, 2)}</textarea>
        <div class="help-text">
          <strong style='color: #ffc107;'>Warning:</strong> Do not paste real secrets here. Use placeholder values. The form below will prompt for the actual secrets, which are not stored in this text block.
        </div>
        <div class="help-text" style="margin-top: 1rem;">
          Configure the command, arguments, and environment variables for your local MCP server.
        </div>
        <div class="json-example">
Example:
${JSON.stringify(exampleConfig, null, 2)}
        </div>
      </div>
    `;
  }

  renderPlaceholderInputs() {
     return html`
      <div class="section" style="margin-top: 1rem;">
        <h4>Provide Environment Variables</h4>
        <p class="help-text">Provide values for the environment variables found in your configuration. These values are not published to the registry but are stored locally for convenience.</p>
        ${this.requiredPlaceholders.map(placeholder => html`
          <div class="form-group">
            <label for="placeholder-${placeholder}">${placeholder}</label>
            <input type="password"
                   id="placeholder-${placeholder}"
                   .value=${this.placeholderValues[placeholder] || ''}
                   @input=${e => this.placeholderValues = { ...this.placeholderValues, [placeholder]: e.target.value }} autocomplete="off">
          </div>
        `)}
      </div>
    `;
  }

  renderRemoteConfig() {
    return html`
      <div class="form-group">
        <label>Remote Server URL</label>
        <input type="url" 
               .value=${this.remoteUrl}
               @input=${(e) => this.remoteUrl = e.target.value}
               placeholder="https://your-mcp-server.com/mcp">
        <div class="help-text">
          Enter the HTTP endpoint for your remote MCP server. OAuth authentication will be handled automatically if required.
        </div>
      </div>
    `;
  }

  renderToolsPreview() {
    return html`
      <div class="tools-preview">
        <h4>Discovered Tools (${this.discoveredTools.length})</h4>
        <div class="form-row">
          <button class="primary" @click=${this.publishServer} ?disabled=${this.loading}>
            ${this.loading ? 'Publishing...' : 'Publish Server'}
          </button>
        </div>
        ${this.discoveredTools.map(tool => html`
          <div class="tool-item">
            <div class="tool-name">${tool.name}</div>
          </div>
        `)}
      </div>
    `;
  }
}

customElements.define('mcp-publisher', McpPublisher);
