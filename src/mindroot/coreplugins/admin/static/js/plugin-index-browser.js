import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';

export class PluginIndexBrowser extends PluginBase {
  static properties = {
    ...PluginBase.properties,
    indices: { type: Array },
    selectedIndex: { type: Object },
    indexPlugins: { type: Array }
  }

  static styles = [
    PluginBase.styles,
    css`
      .index-selector {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
      }

      .index-card {
        background: rgb(20, 20, 40);
        padding: 10px;
        border-radius: 4px;
        cursor: pointer;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.2s ease;
      }

      .index-card:hover {
        background: rgb(30, 30, 60);
      }

      .index-card.selected {
        border-color: #4a90e2;
      }

      .index-card .name {
        font-weight: bold;
      }

      .index-card .description {
        font-size: 0.9em;
        color: #888;
        margin-top: 5px;
      }

      .plugin-item .source-index {
        font-size: 0.9em;
        color: #4a90e2;
      }

      .install-button {
        background: #2ecc71;
        color: white;
        border: none;
        padding: 5px 15px;
        border-radius: 4px;
        cursor: pointer;
        transition: background 0.2s ease;
      }

      .install-button:hover {
        background: #27ae60;
      }

      .install-button:disabled {
        background: #888;
        cursor: not-allowed;
      }
    `
  ];

  constructor() {
    super();
    this.indices = [];
    this.selectedIndex = null;
    this.indexPlugins = [];
    this.fetchIndices();
  }

  async fetchIndices() {
    this.loading = true;
    try {
      const result = await this.apiCall('/index/list-indices');
      this.indices = result.data;
    } catch (error) {
      console.error('Failed to fetch indices:', error);
    } finally {
      this.loading = false;
    }
  }

  async selectIndex(index) {
    this.selectedIndex = index;
    this.loading = true;
    try {
      // Assuming the index data includes plugins directly
      this.indexPlugins = index.plugins || [];
    } catch (error) {
      console.error('Failed to fetch index plugins:', error);
    } finally {
      this.loading = false;
    }
  }

  async handleInstall(plugin) {
    if (plugin.source === 'github') {
      try {
        console.log('Installing plugin from GitHub:', {plugin})
        await this.apiCall('/plugin-manager/install-x-github-plugin', 'POST', {
          plugin: plugin.name,
          url: plugin.github_url
        });
        alert('Plugin installed successfully from GitHub');
      } catch (error) {
        alert(`Failed to install plugin from GitHub: ${error.message}`);
      }
    } else {
      try {
        await this.apiCall('/plugin-manager/install-local-plugin', 'POST', {
          plugin: plugin.name
        });
        // Dispatch event for parent components to refresh their lists
        this.dispatch('plugin-installed', { plugin });
      } catch (error) {
        alert(`Failed to install plugin ${plugin.name}: ${error.message}`);
      }
    }
  }

  renderIndexSelector() {
    return html`
      <div class="index-selector">
        ${this.indices.map(index => html`
          <div class="index-card ${this.selectedIndex?.name === index.name ? 'selected' : ''}"
               @click=${() => this.selectIndex(index)}>
            <div class="name">${index.name}</div>
            ${index.description ? html`
              <div class="description">${index.description}</div>
            ` : ''}
          </div>
        `)}
      </div>
    `;
  }

  renderPluginActions(plugin) {
    const isInstallable = !plugin.installed; // You'll need to track installed state
    return html`
      <button class="install-button"
              ?disabled=${!isInstallable}
              @click=${() => this.handleInstall(plugin)}>
        ${isInstallable ? 'Install' : 'Installed'}
      </button>
    `;
  }

  _render() {
    if (this.loading) return this.renderLoading();

    return html`
      <div class="index-browser">
        ${this.renderIndexSelector()}

        ${this.selectedIndex ? html`
          <input type="text"
                 class="search-box"
                 placeholder="Search plugins in ${this.selectedIndex.name}..."
                 .value=${this.searchTerm}
                 @input=${e => this.searchTerm = e.target.value}>

          ${this.filterPlugins(this.indexPlugins, this.searchTerm).map(plugin =>
            this.renderPlugin(plugin, (plugin) => this.renderPluginActions(plugin))
          )}
        ` : html`
          <p>Select an index to browse available plugins.</p>
        `}
      </div>
    `;
  }
}

customElements.define('plugin-index-browser', PluginIndexBrowser);
