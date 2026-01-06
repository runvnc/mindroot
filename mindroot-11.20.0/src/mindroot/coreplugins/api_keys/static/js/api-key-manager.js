import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class ApiKeyManager extends BaseEl {
  static properties = {
    apiKeys: { type: Array },
    loading: { type: Boolean },
    selectedUser: { type: String }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .api-key-manager {
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

    .key-list {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }

    .key-list th,
    .key-list td {
      padding: 0.75rem;
      text-align: left;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .key-list th {
      background: rgba(0, 0, 0, 0.2);
      font-weight: 500;
    }

    .actions {
      display: flex;
      gap: 10px;
      align-items: center;
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

    button.delete {
      background: #402a2a;
    }

    button.delete:hover {
      background: #503a3a;
    }

    .user-select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      margin-right: 10px;
    }

    .description-input {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      margin-right: 10px;
      width: 200px;
    }

    .key-value {
      font-family: monospace;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
    }
  `;

  constructor() {
    super();
    this.apiKeys = [];
    this.loading = false;
    this.selectedUser = '';
    this.fetchInitialData();
  }

  async fetchInitialData() {
    this.loading = true;
    await Promise.all([
      this.fetchApiKeys(),
    ]);
    this.loading = false;
  }

  async fetchApiKeys() {
    try {
      const response = await fetch('/api_keys/list');
      const result = await response.json();
      if (result.success) {
        this.apiKeys = result.data;
      }
    } catch (error) {
      console.error('Error fetching API keys:', error);
    }
  }

  async handleCreateKey() {
    const description = this.shadowRoot.querySelector('.description-input').value;
    const username = this.shadowRoot.querySelector('.user-select').value;

    try {
      const response = await fetch('/api_keys/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          description
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchApiKeys();
        this.shadowRoot.querySelector('.description-input').value = '';
      }
    } catch (error) {
      console.error('Error creating API key:', error);
    }
  }

  async handleDeleteKey(apiKey) {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      const response = await fetch(`/api_keys/delete/${apiKey}`, {
        method: 'DELETE'
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchApiKeys();
      }
    } catch (error) {
      console.error('Error deleting API key:', error);
    }
  }

  render() {
    return html`
      <div class="api-key-manager">
        <div class="section">
          <div class="actions">
            <input type="text"
                   class="user-select"
                   placeholder="user"
            >
            <input 
              type="text" 
              class="description-input" 
              placeholder="Key description"
            >
            <button @click=${this.handleCreateKey}>Create New API Key</button>
          </div>

          <table class="key-list">
            <thead>
              <tr>
                <th>API Key</th>
                <th>Username</th>
                <th>Description</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${this.apiKeys.map(key => html`
                <tr>
                  <td><span class="key-value">${key.key}</span></td>
                  <td>${key.username}</td>
                  <td>${key.description}</td>
                  <td>${new Date(key.created_at).toLocaleString()}</td>
                  <td>
                    <button 
                      class="delete" 
                      @click=${() => this.handleDeleteKey(key.key)}
                    >Delete</button>
                  </td>
                </tr>
              `)}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }
}

customElements.define('api-key-manager', ApiKeyManager);
