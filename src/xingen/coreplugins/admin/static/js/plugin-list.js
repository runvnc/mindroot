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
        font-weight: 500;
        margin: 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .category-header .material-icons {
        font-size: 1.2em;
        opacity: 0.8;
      }

      .plugin-count {
        font-size: 0.9em;
        color: rgba(255, 255, 255, 0.6);
        margin-left: auto;
      }

      .search-wrapper {
        position: relative;
        margin-bottom: 0.75rem;
      }

      .search-wrapper .material-icons {
        position: absolute;
        left: 1rem;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(255, 255, 255, 0.4);
      }

      .search-box {
        padding: 0.5rem 1rem 0.5rem 2.5rem;
        width: 100%;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
      }

      .no-plugins {
        text-align: center;
        padding: 1.5rem;
        color: rgba(255, 255, 255, 0.6);
        background: rgba(255, 255, 255, 0.03);
        border-radius: 6px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
      }

      .action-button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: rgba(255, 255, 255, 0.1);
        color: #fff;
        cursor: pointer;
        font-size: 0.9rem;
      }

      .action-button:hover {
        background: rgba(255, 255, 255, 0.2);
      }

      .action-button .material-icons {
        font-size: 1.1rem;
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
      this.renderError(`Failed to toggle plugin ${plugin.name}: ${error.message}`);
    }
  }

  async handleUpdate(plugin) {
    try {
      //await this.apiCall('/plugin-manager/update-plugin', 'POST', {
      await this.apiCall('/plugin-manager/install-local-plugin', 'POST', {
        plugin: plugin.name
      });
      await this.fetchPlugins();
    } catch (error) {
      this.renderError(`Failed to update plugin ${plugin.name}: ${error.message}`);
    }
  }

  renderPluginActions(plugin) {
    return html`
      <button class="action-button" @click=${() => this.handleUpdate(plugin)}>
        <span class="material-icons">update</span>
        Update
      </button>
      <button class="action-button" @click=${() => this.handleToggle(plugin)}>
        <span class="material-icons">${plugin.enabled ? 'toggle_off' : 'toggle_on'}</span>
        ${plugin.enabled ? 'Disable' : 'Enable'}
      </button>
    `;
  }

  _render() {
    if (this.loading) return this.renderLoading();

    const filteredPlugins = this.filterPlugins(this.plugins, this.searchTerm);

    return html`
      <div class="plugin-list">
        <div class="search-wrapper">
          <span class="material-icons">search</span>
          <input type="text"
                 class="search-box"
                 placeholder="Search plugins..."
                 .value=${this.searchTerm}
                 @input=${e => this.searchTerm = e.target.value}>
        </div>

        <div class="category-header">
          <span class="material-icons">
            ${this.category === 'core' ? 'settings' : 'extension'}
          </span>
          ${this.category === 'core' ? 'Core' : 'Installed'} Plugins
          <span class="plugin-count">${filteredPlugins.length} plugins</span>
        </div>

        ${filteredPlugins.length ? filteredPlugins.map(plugin => this.renderPlugin(
          plugin,
          (plugin) => this.renderPluginActions(plugin)
        )) : html`
          <div class="no-plugins">
            No ${this.category} plugins found${this.searchTerm ? ' matching your search' : ''}.
          </div>
        `}
      </div>
    `;
  }
}

customElements.define('plugin-list', PluginList);
