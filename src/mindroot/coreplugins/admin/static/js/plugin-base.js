import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class PluginBase extends BaseEl {
  static properties = {
    plugins: { type: Array },
    searchTerm: { type: String },
    loading: { type: Boolean }
  }

  static styles = css`
    .plugin-item {
      background: rgb(15, 15, 30);
      padding: 1rem;
      margin-bottom: 0.75rem;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      display: grid;
      grid-template-columns: minmax(200px, 2fr) auto 1fr auto;
      gap: 1rem;
      align-items: center;
    }

    .plugin-item:hover {
      background: rgb(20, 20, 40);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .plugin-info {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .plugin-name {
      font-weight: 500;
      font-size: 1.1rem;
      color: #fff;
    }

    .plugin-version {
      font-family: 'SF Mono', 'Consolas', monospace;
      color: rgba(255, 255, 255, 0.7);
      background: rgba(255, 255, 255, 0.1);
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      font-size: 0.9rem;
      width: fit-content;
    }

    .plugin-description {
      color: rgba(255, 255, 255, 0.7);
      font-size: 0.9rem;
      grid-column: 3;
    }

    .plugin-actions {
      display: flex;
      gap: 0.5rem;
      justify-content: flex-end;
    }

    .plugin-actions button {
      padding: 0.4rem 0.8rem;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
      cursor: pointer;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }

    .plugin-actions button:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .plugin-actions button .material-icons {
      font-size: 1rem;
    }

    .search-box {
      width: 100%;
      padding: 0.75rem 1rem;
      margin-bottom: 1rem;
      background: rgb(25, 25, 50);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }

    .search-box:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgb(30, 30, 60);
    }

    .loading {
      text-align: center;
      padding: 2rem;
      color: rgba(255, 255, 255, 0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
    }

    .loading .material-icons {
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      100% { transform: rotate(360deg); }
    }

    .error {
      color: #ff6b6b;
      padding: 1rem;
      border-radius: 6px;
      margin: 1rem 0;
      background: rgba(255, 107, 107, 0.1);
      border: 1px solid rgba(255, 107, 107, 0.2);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .status-indicator {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      margin-right: 0.5rem;
    }

    .status-enabled {
      background: #4caf50;
    }

    .status-disabled {
      background: #f44336;
    }
  `;

  constructor() {
    super();
    this.plugins = [];
    this.searchTerm = '';
    this.loading = false;
  }

  async apiCall(endpoint, method = 'GET', body = null) {
    try {
      const options = {
        method,
        headers: { 'Content-Type': 'application/json' }
      };
      if (body) {
        options.body = JSON.stringify(body);
      }

      const response = await fetch(endpoint, options);
      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || 'API call failed');
      }

      return result;
    } catch (error) {
      console.error('API call failed:', error);
      throw error;
    }
  }

  filterPlugins(plugins, searchTerm) {
    if (!searchTerm) return plugins;
    const term = searchTerm.toLowerCase();
    return plugins.filter(plugin => 
      plugin.name.toLowerCase().includes(term) ||
      plugin.description?.toLowerCase().includes(term)
    );
  }

  renderPlugin(plugin, actions) {
    return html`
      <div class="plugin-item">
        <div class="plugin-info">
          <div class="plugin-name">
            <span class="status-indicator ${plugin.enabled ? 'status-enabled' : 'status-disabled'}"></span>
            ${plugin.name}
          </div>
        </div>
        <div class="plugin-version">v${plugin.version || '0.0.1'}</div>
        ${plugin.description ? html`
          <div class="plugin-description">${plugin.description}</div>
        ` : html`<div></div>`}
        <div class="plugin-actions">
          ${actions(plugin)}
        </div>
      </div>
    `;
  }

  renderLoading() {
    return html`
      <div class="loading">
        <span class="material-icons">refresh</span>
        Loading plugins...
      </div>
    `;
  }

  renderError(message) {
    return html`
      <div class="error">
        <span class="material-icons">error_outline</span>
        ${message}
      </div>
    `;
  }
}
