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
    oauthWindow: { type: Object }
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
      this.error = '';
    } catch (error) {
      this.error = 'Invalid JSON configuration';
    }
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

    // Create temporary MCP server to test connection and get tools
    const tempServer = {
      name: `temp_${Date.now()}`,
      description: 'Temporary server for tool discovery',
      command: this.localConfig.command,
      args: this.localConfig.args,
      env: this.localConfig.env,
      transport: 'stdio'
    };

    const response = await fetch('/admin/mcp/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tempServer)
    });

    if (!response.ok) {
      throw new Error('Failed to create temporary server');
    }

    try {
      // Connect to get capabilities
      const connectResponse = await fetch('/admin/mcp/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: tempServer.name })
      });

      if (!connectResponse.ok) {
        throw new Error('Failed to connect to server');
      }

      // Get server info with capabilities
      const listResponse = await fetch('/admin/mcp/list');
      if (listResponse.ok) {
        const data = await listResponse.json();
        const server = data.data.find(s => s.name === tempServer.name);
        if (server && server.capabilities && server.capabilities.tools) {
          this.discoveredTools = server.capabilities.tools;
        }
      }
    } finally {
      // Clean up temporary server
      await fetch('/admin/mcp/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: tempServer.name })
      });
    }
  }

  async discoverRemoteTools() {
    if (!this.remoteUrl) {
      throw new Error('URL is required for remote servers');
    }

    // Use the new backend endpoint that handles OAuth
    const response = await fetch('/admin/mcp/test-remote', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: this.remoteUrl,
        name: this.serverName
      })
    });

    const data = await response.json();

    if (data.success) {
      // Successfully connected without OAuth
      this.discoveredTools = data.tools || [];
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
        if (!this.discoveredTools.length) {
          this.error = 'OAuth window was closed before completion';
          this.loading = false;
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
        this.success = 'OAuth authorization received, completing flow...';
        
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

        if (data.success) {
          this.discoveredTools = data.tools || [];
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

    this.loading = true;
    this.error = "";
    this.success = "";

    try {
      // Prepare server configuration based on type
      const requestData = {
        name: this.serverName,
        description: this.serverDescription,
        server_type: this.serverType,
        tools: this.discoveredTools,
        transport: this.serverType === 'local' ? 'stdio' : 'http',
        auth_type: this.serverType === 'local' ? 'none' : this.authType
      };
      
      // Add type-specific configuration
      if (this.serverType === "local") {
        Object.assign(requestData, {
          command: this.localConfig.command,
          args: this.localConfig.args,
          env: this.localConfig.env
        });
      } else {
        Object.assign(requestData, {
          url: this.remoteUrl
        });
      }

      const response = await fetch("/admin/mcp/publish", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(requestData)
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
      args: ["@modelcontextprotocol/server-filesystem", "/path/to/files"],
      env: {}
    };

    return html`
      <div class="form-group">
        <label>Local Server Configuration (JSON)</label>
        <textarea @input=${this.handleLocalConfigChange}
                 placeholder="Enter JSON configuration...">
        </textarea>
        <div class="help-text">
          Configure the command, arguments, and environment variables for your local MCP server.
        </div>
        <div class="json-example">
Example:
${JSON.stringify(exampleConfig, null, 2)}
        </div>
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
            <div class="tool-description">${tool.description || 'No description available'}</div>
          </div>
        `)}
      </div>
    `;
  }
}

customElements.define('mcp-publisher', McpPublisher);
