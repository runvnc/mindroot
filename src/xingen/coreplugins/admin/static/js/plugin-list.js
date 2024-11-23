import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';

export class PluginList extends PluginBase {
  static properties = {
    ...PluginBase.properties,
    category: { type: String } // 'core' or 'installed'
  }

  static styles = [
    PluginBase.styles,
    css`
      .category-header {
        font-size: 1.1em;
        font-weight: bold;
        margin: 15px 0;
        padding-bottom: 5px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }

      .plugin-item .status {
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.9em;
      }

      .plugin-item .status.enabled {
        background: rgba(46, 204, 113, 0.2);
        color: #2ecc71;
      }

      .plugin-item .status.disabled {
        background: rgba(231, 76, 60, 0.2);
        color: #e74c3c;
      }

      .source-info {
        font-size: 0.9em;
        color: #888;
      }
    `
  ];

  constructor() {
    super();
    this.category = 'installed';
    this.fetchPlugins();
  }

  async fetchPlugins() {
    this.loading = true;
    try {
      const result = await this.apiCall('/plugin-manager/get-all-plugins');
      this.plugins = result.data.filter(plugin => 
        this.category === 'core' ? plugin.source === 'core' : plugin.source !== 'core'
      );
    } catch (error) {
      console.error('Failed to fetch plugins:', error);
    } finally {
      this.loading = false;
    }
  }

  async handleToggle(plugin) {
    try {
      await this.apiCall('/plugin-manager/toggle-plugin', 'POST', {
        plugin: plugin.name,
        enabled: !plugin.enabled
      });
      await this.fetchPlugins();
    } catch (error) {
      alert(`Failed to toggle plugin ${plugin.name}: ${error.message}`);
    }
  }

  async handleUpdate(plugin) {
    try {
      await this.apiCall('/plugin-manager/update-plugin', 'POST', {
        plugin: plugin.name
      });
      await this.fetchPlugins();
    } catch (error) {
      alert(`Failed to update plugin ${plugin.name}: ${error.message}`);
    }
  }

  renderPluginActions(plugin) {
    return html`
      <button @click=${() => this.handleUpdate(plugin)}>Update</button>
      <button @click=${() => this.handleToggle(plugin)}>
        ${plugin.enabled ? 'Disable' : 'Enable'}
      </button>
    `;
  }

  _render() {
    if (this.loading) return this.renderLoading();

    const filteredPlugins = this.filterPlugins(this.plugins, this.searchTerm);

    return html`
      <div class="plugin-list">
        <input type="text"
               class="search-box"
               placeholder="Search plugins..."
               .value=${this.searchTerm}
               @input=${e => this.searchTerm = e.target.value}>

        <div class="category-header">
          ${this.category === 'core' ? 'Core' : 'Installed'} Plugins
        </div>

        ${filteredPlugins.length ? filteredPlugins.map(plugin => this.renderPlugin(
          plugin,
          (plugin) => this.renderPluginActions(plugin)
        )) : html`
          <p>No ${this.category} plugins found.</p>
        `}
      </div>
    `;
  }
}

customElements.define('plugin-list', PluginList);
