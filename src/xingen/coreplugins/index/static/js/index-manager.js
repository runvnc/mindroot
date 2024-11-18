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
      <link rel="stylesheet" href="/index/static/css/index-manager.css">
      <div class="index-manager">
        <div class="index-list">
          <button class="create-index" @click=${this.createNewIndex}>
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
              <h3>Plugins</h3>
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
              <h3>Agents</h3>
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
    `;
  }
}

customElements.define('index-manager', IndexManager);
