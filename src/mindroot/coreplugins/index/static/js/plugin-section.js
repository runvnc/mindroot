import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class PluginSection extends BaseEl {
  static properties = {
    selectedIndex: { type: Object },
    availablePlugins: { type: Object },
    loading: { type: Boolean },
    searchTerm: { type: String }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .section-title {
      font-size: 1.2rem;
      margin-bottom: 1rem;
      color: #ecf0f1;
    }

    .search-box {
      width: 100%;
      padding: 8px;
      margin-bottom: 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: white;
    }

    .plugin-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .plugin-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .plugin-info {
      flex-grow: 1;
    }

    .plugin-name {
      font-weight: bold;
      color: #3498db;
    }

    .plugin-description {
      font-size: 0.9rem;
      color: #95a5a6;
    }

    .plugin-source {
      font-size: 0.8rem;
      color: #7f8c8d;
    }

    .action-button {
      padding: 4px 12px;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      transition: background 0.2s;
    }

    .add-button {
      background: #27ae60;
      color: white;
    }

    .add-button:hover {
      background: #2ecc71;
    }

    .remove-button {
      background: #c0392b;
      color: white;
    }

    .remove-button:hover {
      background: #e74c3c;
    }

    .disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `;

  constructor() {
    super();
    this.searchTerm = '';
  }

  filterPlugins(plugins) {
    if (!plugins) return [];
    const searchLower = this.searchTerm?.toLowerCase() || '';
    return plugins.filter(plugin => 
      // Filter out local plugins
      plugin.source !== 'local' && 
      // Apply search filter
      (plugin.name.toLowerCase().includes(searchLower) ||
       plugin.description?.toLowerCase().includes(searchLower))
    );
  }

  async handleAddPlugin(plugin) {
    try {
      const response = await fetch(`/index/add-plugin/${this.selectedIndex.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(plugin)
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('plugin-added', { detail: plugin }));
      } else {
        console.error('Failed to add plugin:', result.message);
      }
    } catch (error) {
      console.error('Error adding plugin:', error);
    }
  }

  async handleRemovePlugin(pluginName) {
    try {
      const response = await fetch(
        `/index/remove-plugin/${this.selectedIndex.name}/${pluginName}`,
        { method: 'DELETE' }
      );

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('plugin-removed', { 
          detail: { name: pluginName } 
        }));
      } else {
        console.error('Failed to remove plugin:', result.message);
      }
    } catch (error) {
      console.error('Error removing plugin:', error);
    }
  }

  renderPluginList(plugins, isIndexPlugins = false) {
    return html`
      <div class="plugin-list">
        ${this.filterPlugins(plugins).map(plugin => html`
          <div class="plugin-item">
            <div class="plugin-info">
              <div class="plugin-name">${plugin.name}</div>
              ${plugin.description ? html`
                <div class="plugin-description">${plugin.description}</div>
              ` : ''}
              <div class="plugin-source">Source: ${plugin.source}</div>
            </div>
            ${isIndexPlugins ? html`
              <button class="action-button remove-button"
                      @click=${() => this.handleRemovePlugin(plugin.name)}>
                Remove
              </button>
            ` : html`
              <button class="action-button add-button"
                      ?disabled=${this.selectedIndex?.plugins?.some(p => p.name === plugin.name)}
                      @click=${() => this.handleAddPlugin(plugin)}>
                Add
              </button>
            `}
          </div>
        `)}
      </div>
    `;
  }

  render() {
    if (!this.selectedIndex) return null;

    return html`
      <div>
        <h3 class="section-title">Plugins</h3>
        <input type="text"
               class="search-box"
               placeholder="Search plugins..."
               .value=${this.searchTerm || ''}
               @input=${e => this.searchTerm = e.target.value}>

        <h4>Index Plugins</h4>
        ${this.renderPluginList(this.selectedIndex.plugins, true)}

        <h4>Available Plugins</h4>
        ${this.renderPluginList([...this.availablePlugins.core, 
                                ...this.availablePlugins.installed,
                                ...this.availablePlugins.available])}
      </div>
    `;
  }
}

customElements.define('plugin-section', PluginSection);
