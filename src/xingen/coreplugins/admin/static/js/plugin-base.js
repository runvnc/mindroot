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
      padding: 15px;
      margin-bottom: 10px;
      border-radius: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
    }

    .plugin-item span {
      margin-right: 10px;
      margin-bottom: 5px;
    }

    .plugin-item button {
      margin-left: 5px;
    }

    .search-box {
      width: 100%;
      padding: 8px;
      margin-bottom: 15px;
      background: rgb(25, 25, 50);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: #f0f0f0;
    }

    .loading {
      text-align: center;
      padding: 20px;
      font-style: italic;
      color: #888;
    }

    .error {
      color: #ff6b6b;
      padding: 10px;
      border-radius: 4px;
      margin: 10px 0;
    }
  `;

  constructor() {
    super();
    this.plugins = [];
    this.searchTerm = '';
    this.loading = false;
  }

  // Utility method for API calls
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

  // Filter plugins based on search term
  filterPlugins(plugins, searchTerm) {
    if (!searchTerm) return plugins;
    const term = searchTerm.toLowerCase();
    return plugins.filter(plugin => 
      plugin.name.toLowerCase().includes(term) ||
      plugin.description?.toLowerCase().includes(term)
    );
  }

  // Common plugin display template
  renderPlugin(plugin, actions) {
    return html`
      <div class="plugin-item">
        <span class="name">${plugin.name}</span>
        <span class="version">v${plugin.version || '0.0.1'}</span>
        ${plugin.description ? html`
          <span class="description">${plugin.description}</span>
        ` : ''}
        <div class="actions">
          ${actions(plugin)}
        </div>
      </div>
    `;
  }

  // Loading indicator
  renderLoading() {
    return html`
      <div class="loading">
        Loading...
      </div>
    `;
  }

  // Error display
  renderError(message) {
    return html`
      <div class="error">
        ${message}
      </div>
    `;
  }
}
