import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class IndexManager extends BaseEl {
  static properties = {
    indices: { type: Array },
    selectedIndex: { type: Object },
  }

  static styles = [
    css`
      .index-manager {
        display: flex;
        gap: 20px;
        padding: 15px;
      }

      .index-list {
        flex: 1;
        max-width: 300px;
        border-right: 1px solid var(--border-color, #444);
        padding-right: 15px;
      }

      .index-content {
        flex: 2;
      }

      .create-index {
        width: 100%;
        padding: 10px;
        margin-bottom: 15px;
        background: var(--primary-color, #2196F3);
        border: none;
        border-radius: 4px;
        color: white;
        cursor: pointer;
      }

      .index-entry {
        padding: 10px;
        margin: 5px 0;
        border: 1px solid var(--border-color, #444);
        border-radius: 4px;
        cursor: pointer;
      }

      .index-entry.selected {
        background: var(--selected-bg, #2196F3);
        color: white;
      }

      .index-metadata {
        margin-bottom: 20px;
      }

      .index-metadata input {
        width: 100%;
        padding: 8px;
        margin: 5px 0;
        background: var(--input-bg, #333);
        border: 1px solid var(--border-color, #444);
        border-radius: 4px;
        color: var(--text-color, #fff);
      }

      .content-section {
        margin: 15px 0;
        padding: 15px;
        border: 1px solid var(--border-color, #444);
        border-radius: 4px;
      }

      .content-section h3 {
        margin-bottom: 10px;
        font-size: 1.1em;
      }

      .add-button {
        padding: 8px 15px;
        background: var(--secondary-color, #4CAF50);
        border: none;
        border-radius: 4px;
        color: white;
        cursor: pointer;
        margin: 10px 0;
      }

      .item-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .item-entry {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px;
        border: 1px solid var(--border-color, #444);
        border-radius: 4px;
      }

      .item-entry button {
        padding: 5px 10px;
        background: var(--danger-color, #f44336);
        border: none;
        border-radius: 4px;
        color: white;
        cursor: pointer;
      }
    `
  ];

  constructor() {
    super();
    console.log('Index Manager constructed')
    this.indices = [];
    this.selectedIndex = null;
    this.fetchIndices();
  }

  async fetchIndices() {
    try {
      const response = await fetch('/index/list-indices');
      const result = await response.json();
      if (result.success) {
        this.indices = result.data;
      } else {
        console.error('Failed to fetch indices:', result.message);
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

  async addPlugin() {
    if (!this.selectedIndex) return;

    // TODO: Show modal with available plugins from plugin_manifest.json
    const pluginName = prompt('Enter plugin name:');
    if (!pluginName) return;

    try {
      const response = await fetch('/index/add-plugin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          plugin: pluginName
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

  async addAgent() {
    if (!this.selectedIndex) return;

    const agentName = prompt('Enter agent name:');
    if (!agentName) return;

    try {
      const response = await fetch('/index/add-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          index: this.selectedIndex.name,
          agent: agentName
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

  _render() {
    return html`
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
              <button class="add-button" @click=${this.addPlugin}>
                Add Plugin
              </button>
              <div class="item-list">
                ${this.selectedIndex.plugins?.map(plugin => html`
                  <div class="item-entry">
                    <span>${plugin.name}</span>
                    <button @click=${() => this.removePlugin(plugin)}>Remove</button>
                  </div>
                `) || ''}
              </div>
            </div>

            <div class="content-section">
              <h3>Agents</h3>
              <button class="add-button" @click=${this.addAgent}>
                Add Agent
              </button>
              <div class="item-list">
                ${this.selectedIndex.agents?.map(agent => html`
                  <div class="item-entry">
                    <span>${agent.name}</span>
                    <button @click=${() => this.removeAgent(agent)}>Remove</button>
                  </div>
                `) || ''}
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

console.log('Index Manager defined')

