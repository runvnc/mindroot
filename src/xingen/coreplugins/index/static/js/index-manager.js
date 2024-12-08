import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';
import './index-list.js';
import './index-metadata.js';
import './plugin-section.js';
import './agent-section.js';
import './components/upload-area.js';
import './components/publish-button.js';

class IndexManager extends BaseEl {
  static properties = {
    indices: { type: Array },
    selectedIndex: { type: Object },
    availablePlugins: { type: Object },
    availableAgents: { type: Array },
    loading: { type: Boolean }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .index-manager {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1600px;
      margin: 0 auto;
      height: calc(100vh - 100px);
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      gap: 20px;
      height: 100%;
      min-height: 0;
    }

    .index-content {
      flex: 1;
      overflow-y: auto;
      padding-right: 10px;
      display: flex;
      flex-direction: column;
      gap: 15px;
      min-height: 0;
    }

    .index-content > * {
      flex-shrink: 0;
    }

    .actions-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
    }

    /* Scrollbar styling */
    .index-content::-webkit-scrollbar {
      width: 8px;
    }

    .index-content::-webkit-scrollbar-track {
      background: rgba(10, 10, 25, 0.95);
    }

    .index-content::-webkit-scrollbar-thumb {
      background-color: #333;
      border-radius: 10px;
      border: 2px solid rgba(10, 10, 25, 0.95);
    }

    .index-content::-webkit-scrollbar-thumb:hover {
      background-color: #444;
    }
  `;
  constructor() {
    super();
    this.indices = [];
    this.selectedIndex = null;
    this.availablePlugins = { core: [], installed: [], available: [] };
    this.availableAgents = [];
    this.loading = false;
    this.fetchInitialData();
  }

  async fetchInitialData() {
    this.loading = true;
    await Promise.all([
      this.fetchIndices(),
      this.fetchAvailablePlugins(),
      this.fetchAvailableAgents()
    ]);
    this.loading = false;
  }

  async fetchIndices() {
    try {
      const response = await fetch('/index/list-indices');
      const result = await response.json();
      if (result.success) {
        this.indices = result.data;
      }
    } catch (error) {
      console.error('Error fetching indices:', error);
    }
  }

  async fetchAvailablePlugins() {
    try {
      const response = await fetch('/plugin-manager/get-all-plugins');
      const result = await response.json();
      if (result.success) {
        const categorized = { core: [], installed: [], available: [] };
        result.data.forEach(plugin => {
          // Skip local plugins
          if (plugin.source === 'local') return;
          
          if (plugin.source === 'core') {
            categorized.core.push(plugin);
          } else if (plugin.state === 'installed') {
            categorized.installed.push(plugin);
          } else {
            categorized.available.push(plugin);
          }
        });
        this.availablePlugins = categorized;
      }
    } catch (error) {
      console.error('Error fetching plugins:', error);
    }
  }

  async fetchAvailableAgents() {
    try {
      const response = await fetch('/agents/local');
      const agents = await response.json();
      this.availableAgents = agents;
    } catch (error) {
      console.error('Error fetching agents:', error);
    }
  }

  handleIndexSelected(e) {
    this.selectedIndex = e.detail;
  }

  handleIndexCreated(e) {
    this.fetchIndices();
  }

  handleMetadataUpdated(e) {
    const { field, value } = e.detail;
    this.selectedIndex = { ...this.selectedIndex, [field]: value };
  }

  handlePluginAdded(e) {
    this.fetchIndices();
  }

  handlePluginRemoved(e) {
    this.fetchIndices();
  }

  handleAgentAdded(e) {
    this.fetchIndices();
  }

  handleAgentRemoved(e) {
    this.fetchIndices();
  }

  handleIndexInstalled(e) {
    this.fetchIndices();
  }

  handlePublishSuccess(e) {
    const { message, zipFile } = e.detail;
    // You could show a notification here if desired
    console.log(`Index published successfully: ${zipFile}`);
  }

  render() {
    return html`
      <div class="index-manager">
        <upload-area
          @index-installed=${this.handleIndexInstalled}>
        </upload-area>

        <div class="section">
          <index-list 
            .indices=${this.indices}
            .selectedIndex=${this.selectedIndex}
            .loading=${this.loading}
            @index-selected=${this.handleIndexSelected}
            @index-created=${this.handleIndexCreated}>
          </index-list>

          <div class="index-content">
            ${this.selectedIndex ? html`
              <div class="actions-bar">
                <publish-button
                  .indexName=${this.selectedIndex.name}
                  @publish-success=${this.handlePublishSuccess}>
                </publish-button>
              </div>

              <index-metadata
                .selectedIndex=${this.selectedIndex}
                .loading=${this.loading}
                @metadata-updated=${this.handleMetadataUpdated}>
              </index-metadata>

              <plugin-section
                .selectedIndex=${this.selectedIndex}
                .availablePlugins=${this.availablePlugins}
                .loading=${this.loading}
                @plugin-added=${this.handlePluginAdded}
                @plugin-removed=${this.handlePluginRemoved}>
              </plugin-section>

              <agent-section
                .selectedIndex=${this.selectedIndex}
                .availableAgents=${this.availableAgents}
                .loading=${this.loading}
                @agent-added=${this.handleAgentAdded}
                @agent-removed=${this.handleAgentRemoved}>
              </agent-section>
            ` : html`
              <p>Select an index from the list or create a new one.</p>
            `}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('index-manager', IndexManager);
