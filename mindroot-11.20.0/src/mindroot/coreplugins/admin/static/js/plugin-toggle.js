import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';

class PluginToggle extends PluginBase {
  static styles = [
    PluginBase.styles,
    css`
      .plugin-toggle {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .toggle-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 10px;
      }

      .toggle-item {
        background: rgb(15, 15, 30);
        padding: 12px;
        border-radius: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }

      .toggle-item .info {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .toggle-item .name {
        font-weight: bold;
      }

      .toggle-item .type {
        font-size: 0.8em;
        color: #888;
      }

      .toggle-switch {
        position: relative;
        display: inline-block;
        width: 48px;
        height: 24px;
      }

      .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
      }

      .toggle-slider {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #444;
        transition: .4s;
        border-radius: 24px;
      }

      .toggle-slider:before {
        position: absolute;
        content: "";
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        transition: .4s;
        border-radius: 50%;
      }

      input:checked + .toggle-slider {
        background-color: #2ecc71;
      }

      input:checked + .toggle-slider:before {
        transform: translateX(24px);
      }

      .actions {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 15px;
      }
    `
  ];

  constructor() {
    super();
    this.fetchPlugins();
  }

  async fetchPlugins() {
    this.loading = true;
    try {
      const result = await this.apiCall('/plugin-manager/get-all-plugins');
      this.plugins = result.data.filter(plugin => 
        plugin.state === 'installed' || plugin.source === 'core'
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

  _render() {
    if (this.loading) return this.renderLoading();

    const filteredPlugins = this.filterPlugins(this.plugins, this.searchTerm);

    return html`
      <div class="plugin-toggle">
        <input type="text"
               class="search-box"
               placeholder="Quick search plugins..."
               .value=${this.searchTerm}
               @input=${e => this.searchTerm = e.target.value}>

        <div class="toggle-list">
          ${filteredPlugins.map(plugin => html`
            <div class="toggle-item">
              <div class="info">
                <span class="name">${plugin.name}</span>
                <span class="type">${plugin.source === 'core' ? 'Core' : 'Installed'}</span>
              </div>
              <label class="toggle-switch">
                <input type="checkbox"
                       ?checked=${plugin.enabled}
                       @change=${() => this.handleToggle(plugin)}>
                <span class="toggle-slider"></span>
              </label>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}

customElements.define('plugin-toggle', PluginToggle);
