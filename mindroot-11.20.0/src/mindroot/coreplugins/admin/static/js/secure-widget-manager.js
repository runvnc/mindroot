import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import showNotification from './notification.js';

class SecureWidgetManager extends BaseEl {
  static properties = {
    agents: { type: Array },
    apiKeys: { type: Array },
    widgets: { type: Array },
    selectedAgent: { type: String },
    selectedApiKey: { type: String },
    domainName: { type: String },
    description: { type: String },
    loading: { type: Boolean },
    showCreateForm: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }
    
    .secure-widget-manager {
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
    
    .section h3 {
      margin: 0 0 1rem 0;
      color: #f0f0f0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .form-group {
      margin-bottom: 15px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 5px;
      color: #f0f0f0;
      font-weight: 500;
    }
    
    input[type="text"],
    textarea,
    select {
      width: 100%;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
      box-sizing: border-box;
    }
    
    textarea {
      resize: vertical;
      min-height: 60px;
    }
    
    button {
      background: #2196F3;
      color: #fff;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-right: 10px;
      font-size: 0.9rem;
    }
    
    button:hover {
      background: #1976D2;
    }
    
    button.secondary {
      background: #2a2a40;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    button.secondary:hover {
      background: #3a3a50;
    }
    
    button.danger {
      background: #f44336;
    }
    
    button.danger:hover {
      background: #d32f2f;
    }
    
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .button-group {
      display: flex;
      gap: 10px;
      margin-top: 15px;
      flex-wrap: wrap;
    }
    
    .widget-list {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }
    
    .widget-list th,
    .widget-list td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      color: #f0f0f0;
    }
    
    .widget-list th {
      background: rgba(0, 0, 0, 0.2);
      font-weight: 500;
    }
    
    .token-display {
      font-family: monospace;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.8rem;
    }
    
    .loading {
      opacity: 0.6;
      pointer-events: none;
    }
    
    .create-form {
      border: 2px solid #2196F3;
      border-radius: 8px;
      padding: 1.5rem;
      margin-bottom: 1rem;
    }
    
    .no-widgets {
      text-align: center;
      color: #888;
      padding: 2rem;
      font-style: italic;
    }
  `;

  constructor() {
    super();
    this.agents = [];
    this.apiKeys = [];
    this.widgets = [];
    this.selectedAgent = '';
    this.selectedApiKey = '';
    this.domainName = window.location.origin;
    this.description = '';
    this.loading = false;
    this.showCreateForm = false;
    
    this.fetchInitialData();
  }

  async fetchInitialData() {
    this.loading = true;
    await Promise.all([
      this.fetchAgents(),
      this.fetchApiKeys(),
      this.fetchWidgets()
    ]);
    this.loading = false;
  }

  async fetchAgents() {
    try {
      const response = await fetch('/agents/local');
      if (!response.ok) throw new Error('Failed to fetch agents');
      this.agents = await response.json();
    } catch (error) {
      showNotification('error', `Error loading agents: ${error.message}`);
    }
  }

  async fetchApiKeys() {
    try {
      const response = await fetch('/api_keys/list');
      if (!response.ok) throw new Error('Failed to fetch API keys');
      const result = await response.json();
      this.apiKeys = result.data || [];
    } catch (error) {
      showNotification('error', `Error loading API keys: ${error.message}`);
    }
  }

  async fetchWidgets() {
    try {
      const response = await fetch('/widgets/list');
      if (!response.ok) throw new Error('Failed to fetch widgets');
      const result = await response.json();
      this.widgets = result.data || [];
    } catch (error) {
      showNotification('error', `Error loading widgets: ${error.message}`);
    }
  }

  handleInputChange(event) {
    const { name, value } = event.target;
    this[name] = value;
  }

  toggleCreateForm() {
    this.showCreateForm = !this.showCreateForm;
    if (!this.showCreateForm) {
      this.selectedAgent = '';
      this.selectedApiKey = '';
      this.description = '';
    }
  }

  async handleCreateWidget() {
    if (!this.selectedAgent || !this.selectedApiKey) {
      showNotification('error', 'Please select both an agent and API key');
      return;
    }

    this.loading = true;
    try {
      const response = await fetch('/widgets/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          api_key: this.selectedApiKey,
          agent_name: this.selectedAgent,
          base_url: this.domainName,
          description: this.description
        })
      });

      const result = await response.json();
      if (result.success) {
        showNotification('success', 'Widget token created successfully!');
        await this.fetchWidgets();
        this.toggleCreateForm();
      } else {
        throw new Error(result.message || 'Failed to create widget token');
      }
    } catch (error) {
      showNotification('error', `Error creating widget: ${error.message}`);
    } finally {
      this.loading = false;
    }
  }

  async handleDeleteWidget(token) {
    if (!confirm('Are you sure you want to delete this widget token?')) {
      return;
    }

    this.loading = true;
    try {
      const response = await fetch(`/widgets/delete/${token}`, {
        method: 'DELETE'
      });

      const result = await response.json();
      if (result.success) {
        showNotification('success', 'Widget token deleted successfully');
        await this.fetchWidgets();
      } else {
        throw new Error(result.message || 'Failed to delete widget token');
      }
    } catch (error) {
      showNotification('error', `Error deleting widget: ${error.message}`);
    } finally {
      this.loading = false;
    }
  }

  copyEmbedCode(token) {
    const embedCode = `<script src="${this.domainName}/chat/embed/${token}"></script>`;
    navigator.clipboard.writeText(embedCode).then(() => {
      showNotification('success', 'Embed code copied to clipboard!');
    }).catch(() => {
      showNotification('error', 'Failed to copy embed code');
    });
  }

  _render() {
    return html`
      <div class="secure-widget-manager ${this.loading ? 'loading' : ''}">
        <div class="section">
          <h3>
            <span class="material-icons">security</span>
            Secure Chat Widget Manager
          </h3>
          <p>Create secure widget tokens for embedding chat on external websites. API keys are never exposed to the frontend.</p>
          
          <div class="button-group">
            <button @click=${this.toggleCreateForm}>
              ${this.showCreateForm ? 'Cancel' : 'Create New Widget Token'}
            </button>
            <button class="secondary" @click=${this.fetchWidgets}>
              Refresh List
            </button>
          </div>
        </div>

        ${this.showCreateForm ? this.renderCreateForm() : ''}
        ${this.renderWidgetList()}
      </div>
    `;
  }

  renderCreateForm() {
    return html`
      <div class="section create-form">
        <h3>
          <span class="material-icons">add</span>
          Create Widget Token
        </h3>
        
        <div class="form-group">
          <label>Select Agent:</label>
          <select name="selectedAgent" @change=${this.handleInputChange} .value=${this.selectedAgent}>
            <option value="">Choose an agent...</option>
            ${this.agents.map(agent => html`<option value="${agent.name}">${agent.name}</option>`)}
          </select>
        </div>

        <div class="form-group">
          <label>Select API Key:</label>
          <select name="selectedApiKey" @change=${this.handleInputChange} .value=${this.selectedApiKey}>
            <option value="">Choose an API key...</option>
            ${this.apiKeys.map(key => html`
              <option value="${key.key}">
                ${key.description || key.key.substring(0, 8) + '...'}
              </option>
            `)}
          </select>
        </div>

        <div class="form-group">
          <label>Domain Name:</label>
          <input type="text" name="domainName" .value=${this.domainName} @input=${this.handleInputChange} 
                 placeholder="https://your-domain.com">
        </div>

        <div class="form-group">
          <label>Description (Optional):</label>
          <textarea name="description" .value=${this.description} @input=${this.handleInputChange} 
                   placeholder="e.g., Widget for company website"></textarea>
        </div>

        <div class="button-group">
          <button @click=${this.handleCreateWidget} ?disabled=${!this.selectedAgent || !this.selectedApiKey}>
            Create Widget Token
          </button>
          <button class="secondary" @click=${this.toggleCreateForm}>
            Cancel
          </button>
        </div>
      </div>
    `;
  }

  renderWidgetList() {
    return html`
      <div class="section">
        <h3>
          <span class="material-icons">widgets</span>
          Your Widget Tokens
        </h3>
        
        ${this.widgets.length === 0 ? html`
          <div class="no-widgets">
            <p>No widget tokens created yet.</p>
            <p>Create your first widget token to get started with secure chat embedding.</p>
          </div>
        ` : html`
          <table class="widget-list">
            <thead>
              <tr>
                <th>Token</th>
                <th>Agent</th>
                <th>Description</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${this.widgets.map(widget => html`
                <tr>
                  <td><span class="token-display">${widget.token}</span></td>
                  <td>${widget.agent_name}</td>
                  <td>${widget.description || 'No description'}</td>
                  <td>${new Date(widget.created_at).toLocaleDateString()}</td>
                  <td>
                    <button class="secondary" @click=${() => this.copyEmbedCode(widget.token)}>
                      Copy Embed Code
                    </button>
                    <button class="danger" @click=${() => this.handleDeleteWidget(widget.token)}>
                      Delete
                    </button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        `}
      </div>
    `;
  }
}

customElements.define('secure-widget-manager', SecureWidgetManager);
