import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';
import './plugin-install-dialog.js';

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

  firstUpdated() {
    super.firstUpdated();
    // Create the install dialog if it doesn't exist
    if (!this.installDialog) {
      this.installDialog = document.createElement('plugin-install-dialog');
      document.body.appendChild(this.installDialog);
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Remove the dialog when component is removed
    if (this.installDialog && document.body.contains(this.installDialog)) {
      document.body.removeChild(this.installDialog);
    }
  }

  async handleInstall(plugin) {
    if (plugin.source === 'github') {
      try {
        console.log('Installing plugin from GitHub:', {plugin})

        // Open the installation dialog
        this.installDialog.open(plugin.name, 'GitHub');
        
        // Connect to SSE endpoint for streaming GitHub installation
        // Build URL with properly encoded parameters
        const params = new URLSearchParams();
        params.append('plugin', plugin.name);
        params.append('source', 'github');
        params.append('source_path', plugin.github_url);
        
        const eventSource = new EventSource(`/plugin-manager/stream-install-plugin?${params.toString()}`);
        
        // Debug
        console.log(`Connected to SSE endpoint: /plugin-manager/stream-install-plugin?${params.toString()}`);
        
        eventSource.addEventListener('message', (event) => {
          console.log('SSE message event:', event.data);
          this.installDialog.addOutput(event.data, 'info');
        });
        
        eventSource.addEventListener('error', (event) => {
          console.log('SSE error event:', event.data);
          this.installDialog.addOutput(event.data, 'error');
        });
        
        eventSource.addEventListener('warning', (event) => {
          console.log('SSE warning event:', event.data);
          this.installDialog.addOutput(event.data, 'warning');
        });
        
        eventSource.addEventListener('complete', (event) => {
          console.log('SSE complete event:', event.data);
          this.installDialog.addOutput(event.data, 'success');
          this.installDialog.setComplete(false);
          eventSource.close();
          // Dispatch event for parent components to refresh their lists
          this.dispatch('plugin-installed', { plugin });
        });
        
        eventSource.onerror = () => {
          console.log('SSE connection error');
          eventSource.close();
          this.installDialog.setComplete(true);
        };
      } catch (error) {
        this.installDialog.addOutput(`Failed to install plugin from GitHub: ${error.message}`, 'error');
        this.installDialog.setComplete(true);
      }
    } else if (plugin.source === 'local') {
      try {
        // Open the installation dialog
        this.installDialog.open(plugin.name, 'Local');
        
        // Use the existing local installation endpoint
        try {
          this.installDialog.addOutput(`Starting installation of ${plugin.name} from local path...`, 'info');
          
          // Make the API call to install the plugin
          await this.apiCall('/plugin-manager/install-local-plugin', 'POST', {
            plugin: plugin.name
          });
          
          // Show success message
          this.installDialog.addOutput(`Plugin ${plugin.name} installed successfully from local path`, 'success');
          this.installDialog.setComplete(false);
          
          // Notify parent components to refresh their lists
          this.dispatch('plugin-installed', { plugin });
        } catch (error) {
          // Show error message
          this.installDialog.addOutput(`Failed to install plugin from local path: ${error.message}`, 'error');
          this.installDialog.setComplete(true);
        }
      } catch (error) {
        this.installDialog.addOutput(`Failed to install plugin ${plugin.name}: ${error.message}`, 'error');
        this.installDialog.setComplete(true);
      }
    } else {
      // For PyPI packages, use the streaming approach
      try {
        // Open the installation dialog
        this.installDialog.open(plugin.name, 'PyPI');
        
        // Connect to SSE endpoint
        // Build URL with properly encoded parameters
        const params = new URLSearchParams();
        params.append('plugin', plugin.name);
        params.append('source', 'pypi');
        
        const eventSource = new EventSource(`/plugin-manager/stream-install-plugin?${params.toString()}`);
        
        // Debug
        console.log(`Connected to SSE endpoint: /plugin-manager/stream-install-plugin?${params.toString()}`);
        
        eventSource.addEventListener('message', (event) => {
          console.log('SSE message event:', event.data);
          this.installDialog.addOutput(event.data, 'info');
        });
        
        eventSource.addEventListener('error', (event) => {
          console.log('SSE error event:', event.data);
          this.installDialog.addOutput(event.data, 'error');
        });
        
        eventSource.addEventListener('warning', (event) => {
          console.log('SSE warning event:', event.data);
          this.installDialog.addOutput(event.data, 'warning');
        });
        
        eventSource.addEventListener('complete', (event) => {
          console.log('SSE complete event:', event.data);
          this.installDialog.addOutput(event.data, 'success');
          this.installDialog.setComplete(false);
          eventSource.close();
          // Dispatch event for parent components to refresh their lists
          this.dispatch('plugin-installed', { plugin });
        });
        
        eventSource.onerror = () => {
          console.log('SSE connection error');
          eventSource.close();
          this.installDialog.setComplete(true);
        };
      } catch (error) {
        this.installDialog.addOutput(`Failed to install plugin ${plugin.name}: ${error.message}`, 'error');
        this.installDialog.setComplete(true);
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
