import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class IndexManager extends BaseEl {
  static properties = {
    indices: { type: Array },
    selectedIndex: { type: Object },
    availablePlugins: { type: Object },
    availableAgents: { type: Array },
    searchPlugins: { type: String },
    searchAgents: { type: String }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .index-manager {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      width: 100%;
      max-width: 1600px;
      margin: 0 auto;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      gap: 20px;
      height: calc(100vh - 200px);
      overflow: hidden;
    }

    .index-list {
      flex: 0 0 300px;
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      padding-right: 15px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .index-content {
      flex: 1;
      overflow-y: auto;
      padding-right: 10px;
    }

    .create-index {
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      background: #2196F3;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 6px;
      color: white;
      cursor: pointer;
      font-size: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: background-color 0.2s;
    }

    .create-index:hover {
      background: #1976D2;
    }

    .index-entries {
      overflow-y: auto;
      flex-grow: 1;
    }

    .index-entry {
      padding: 10px;
      margin: 5px 0;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      background: rgba(255, 255, 255, 0.05);
    }

    .index-entry:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .index-entry.selected {
      background: #2196F3;
      border-color: #1976D2;
      color: white;
    }

    .index-metadata {
      margin-bottom: 20px;
    }

    .index-metadata input {
      width: 100%;
      padding: 10px;
      margin: 5px 0;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }

    .index-metadata input:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }

    .content-section {
      margin: 15px 0;
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
    }

    .content-section h3 {
      margin-bottom: 15px;
      font-size: 1.1em;
      color: #f0f0f0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .split-view {
      display: flex;
      gap: 20px;
      margin-top: 10px;
      min-height: 400px;
      max-height: 600px;
    }

    .available-items, .selected-items {
      flex: 1;
      background: rgb(10, 10, 25);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 6px;
      padding: 15px;
      display: flex;
      flex-direction: column;
    }

    .available-items h4, .selected-items h4 {
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      color: #f0f0f0;
      font-size: 1rem;
      flex-shrink: 0;
    }

    .search-box {
      width: 100%;
      padding: 8px 12px;
      margin-bottom: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
      flex-shrink: 0;
    }

    .search-box:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }

    .category-group {
      margin-bottom: 15px;
    }

    .category-title {
      font-size: 0.9em;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 8px;
      padding: 5px 8px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 4px;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .item-list {
      display: flex;
      flex-direction: column;
      gap: 5px;
      overflow-y: auto;
      flex-grow: 1;
      padding-right: 5px;
    }

    .item-entry {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 6px;
      transition: all 0.2s;
    }

    .item-entry:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .item-entry .name {
      flex: 1;
      color: #f0f0f0;
    }

    .item-entry .version {
      color: rgba(255, 255, 255, 0.5);
      font-size: 0.9em;
      margin: 0 10px;
      font-family: 'SF Mono', 'Consolas', monospace;
    }

    .item-entry button {
      padding: 4px 12px;
      background: transparent;
      border: 1px solid currentColor;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
      transition: all 0.2s;
    }

    .item-entry button.add {
      color: #4CAF50;
    }

    .item-entry button.remove {
      color: #f44336;
    }

    .item-entry button:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .no-items {
      color: rgba(255, 255, 255, 0.5);
      text-align: center;
      padding: 20px;
      font-style: italic;
    }

    /* Scrollbar styling */
    .item-list::-webkit-scrollbar,
    .index-content::-webkit-scrollbar,
    .index-entries::-webkit-scrollbar {
      width: 8px;
    }

    .item-list::-webkit-scrollbar-track,
    .index-content::-webkit-scrollbar-track,
    .index-entries::-webkit-scrollbar-track {
      background: rgba(10, 10, 25, 0.95);
    }

    .item-list::-webkit-scrollbar-thumb,
    .index-content::-webkit-scrollbar-thumb,
    .index-entries::-webkit-scrollbar-thumb {
      background-color: #333;
      border-radius: 10px;
      border: 2px solid rgba(10, 10, 25, 0.95);
    }

    .item-list::-webkit-scrollbar-thumb:hover,
    .index-content::-webkit-scrollbar-thumb:hover,
    .index-entries::-webkit-scrollbar-thumb:hover {
      background-color: #444;
    }
  `;

  constructor() {
    super();
    console.log('Index Manager constructed')
    this.indices = [];
    this.selectedIndex = null;
    this.availablePlugins = { core: [], installed: [], available: [] };
    this.availableAgents = [];
    this.searchPlugins = '';
    this.searchAgents = '';
    this.fetchIndices();
    this.fetchAvailablePlugins();
    this.fetchAvailableAgents();
  }

  async fetchAvailablePlugins() {
    try {
      const response = await fetch('/plugin-manager/get-all-plugins');
      const result = await response.json();
      if (result.success) {
        // Organize plugins by category
        const categorized = { core: [], installed: [], available: [] };
        result.data.forEach(plugin => {
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

  async createNewIndex() {
    const name = prompt('Enter name for new index:');
    if (!name) return;

    try {
      const response = await fetch('/index/create-index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: '',
          version: '1.0.0',
          plugins: [],
          agents: []
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchIndices();
        this.selectIndex(result.data);
      } else {
        alert(`Failed to create index: ${result.message}`);
      }
    } catch (error) {
      console.error('Error creating index:', error);
      alert('Failed to create index');
    }
  }

  selectIndex(index) {
    this.selectedIndex = index;
  }

  async updateIndexMetadata(e) {
    if (!this.selectedIndex) return;

    const field = e.target.name;
    const value = e.target.value;
    
    try {
      const response = await fetch('/index/update-index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.selectedIndex.name,
          [field]: value
        })
      });

      const result = await response.json();
      if (result.success) {
        this.selectedIndex = { ...this.selectedIndex, [field]: value };
      } else {
        alert(`Failed to update index: ${result.message}`);
      }
    } catch (error) {
      console.error('Error updating index:', error);
      alert('Failed to update index');
    }
  }

  async addPlugin(plugin) {
    if (!this.selectedIndex) return;

    try {
      const response = await fetch('/index/add-plugin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          plugin: plugin.name
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchIndices();
        this.selectIndex(result.data);
      } else {
        alert(`Failed to add plugin: ${result.message}`);
      }
    } catch (error) {
      console.error('Error adding plugin:', error);
      alert('Failed to add plugin');
    }
  }

  async addAgent(agent) {
    if (!this.selectedIndex) return;

    try {
      const response = await fetch('/index/add-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          agent: agent.name
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchIndices();
        this.selectIndex(result.data);
      } else {
        alert(`Failed to add agent: ${result.message}`);
      }
    } catch (error) {
      console.error('Error adding agent:', error);
      alert('Failed to add agent');
    }
  }

  async removePlugin(plugin) {
    if (!this.selectedIndex) return;

    try {
      const response = await fetch('/index/remove-plugin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          plugin: plugin.name
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchIndices();
        this.selectIndex(result.data);
      } else {
        alert(`Failed to remove plugin: ${result.message}`);
      }
    } catch (error) {
      console.error('Error removing plugin:', error);
      alert('Failed to remove plugin');
    }
  }

  async removeAgent(agent) {
    if (!this.selectedIndex) return;

    try {
      const response = await fetch('/index/remove-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          agent: agent.name
        })
      });

      const result = await response.json();
      if (result.success) {
        await this.fetchIndices();
        this.selectIndex(result.data);
      } else {
        alert(`Failed to remove agent: ${result.message}`);
      }
    } catch (error) {
      console.error('Error removing agent:', error);
      alert('Failed to remove agent');
    }
  }

  isPluginInIndex(plugin) {
    return this.selectedIndex?.plugins?.some(p => p.name === plugin.name) || false;
  }

  isAgentInIndex(agent) {
    return this.selectedIndex?.agents?.some(a => a.name === agent.name) || false;
  }

  renderAvailablePlugins() {
    const searchTerm = this.searchPlugins.toLowerCase();
    return html`
      ${Object.entries(this.availablePlugins).map(([category, plugins]) => {
        const filteredPlugins = plugins.filter(plugin => 
          plugin.name.toLowerCase().includes(searchTerm)
        );
        if (filteredPlugins.length === 0) return '';
        
        return html`
          <div class="category-group">
            <div class="category-title">${category}</div>
            ${filteredPlugins.map(plugin => html`
              <div class="item-entry">
                <span class="name">${plugin.name}</span>
                <span class="version">${plugin.version || '0.0.1'}</span>
                ${this.isPluginInIndex(plugin)
                  ? html`<button class="remove" @click=${() => this.removePlugin(plugin)}>Remove</button>`
                  : html`<button class="add" @click=${() => this.addPlugin(plugin)}>Add</button>`
                }
              </div>
            `)}
          </div>
        `;
      })}
    `;
  }

  _render() {
    return html`
      <div class="index-manager">
        <div class="section">
          <div class="index-list">
            <button class="create-index" @click=${this.createNewIndex}>
              <span class="material-icons">add</span>
              Create New Index
            </button>
            <div class="index-entries">
              ${this.indices.map(index => html`
                <div class="index-entry ${this.selectedIndex?.name === index.name ? 'selected' : ''}"
                     @click=${() => this.selectIndex(index)}>
                  ${index.name}
                </div>
              `)}
            </div>
          </div>

          <div class="index-content">
            ${this.selectedIndex ? html`
              <div class="index-metadata">
                <input type="text" name="name" 
                       value=${this.selectedIndex.name}
                       @change=${this.updateIndexMetadata}
                       placeholder="Index Name">
                <input type="text" name="description"
                       value=${this.selectedIndex.description || ''}
                       @change=${this.updateIndexMetadata}
                       placeholder="Description">
                <input type="text" name="version"
                       value=${this.selectedIndex.version || '1.0.0'}
                       @change=${this.updateIndexMetadata}
                       placeholder="Version">
              </div>

              <div class="content-section">
                <h3>
                  <span class="material-icons">extension</span>
                  Plugins
                </h3>
                <div class="split-view">
                  <div class="available-items">
                    <h4>Available Plugins</h4>
                    <input type="text" 
                           class="search-box"
                           placeholder="Search plugins..."
                           .value=${this.searchPlugins}
                           @input=${e => this.searchPlugins = e.target.value}>
                    <div class="item-list">
                      ${this.renderAvailablePlugins()}
                    </div>
                  </div>
                  <div class="selected-items">
                    <h4>Index Plugins</h4>
                    <div class="item-list">
                      ${this.selectedIndex.plugins?.length ? this.selectedIndex.plugins.map(plugin => html`
                        <div class="item-entry">
                          <span class="name">${plugin.name}</span>
                          <span class="version">${plugin.version || '0.0.1'}</span>
                          <button class="remove" @click=${() => this.removePlugin(plugin)}>Remove</button>
                        </div>
                      `) : html`
                        <div class="no-items">No plugins in index</div>
                      `}
                    </div>
                  </div>
                </div>
              </div>

              <div class="content-section">
                <h3>
                  <span class="material-icons">smart_toy</span>
                  Agents
                </h3>
                <div class="split-view">
                  <div class="available-items">
                    <h4>Available Agents</h4>
                    <input type="text" 
                           class="search-box"
                           placeholder="Search agents..."
                           .value=${this.searchAgents}
                           @input=${e => this.searchAgents = e.target.value}>
                    <div class="item-list">
                      ${this.availableAgents.length ? this.availableAgents
                        .filter(agent => agent.name.toLowerCase().includes(this.searchAgents.toLowerCase()))
                        .map(agent => html`
                          <div class="item-entry">
                            <span class="name">${agent.name}</span>
                            <span class="version">${agent.version || '0.0.1'}</span>
                            ${this.isAgentInIndex(agent)
                              ? html`<button class="remove" @click=${() => this.removeAgent(agent)}>Remove</button>`
                              : html`<button class="add" @click=${() => this.addAgent(agent)}>Add</button>`
                            }
                          </div>
                        `) : html`
                          <div class="no-items">No agents available</div>
                        `}
                    </div>
                  </div>
                  <div class="selected-items">
                    <h4>Index Agents</h4>
                    <div class="item-list">
                      ${this.selectedIndex.agents?.length ? this.selectedIndex.agents.map(agent => html`
                        <div class="item-entry">
                          <span class="name">${agent.name}</span>
                          <span class="version">${agent.version || '0.0.1'}</span>
                          <button class="remove" @click=${() => this.removeAgent(agent)}>Remove</button>
                        </div>
                      `) : html`
                        <div class="no-items">No agents in index</div>
                      `}
                    </div>
                  </div>
                </div>
              </div>
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
