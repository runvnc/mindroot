import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import showNotification from './notification.js';

class IndexedAgents extends BaseEl {
  static properties = {
    indexedAgents: { type: Array },
    searchIndexed: { type: String },
    scope: { type: String },
    loading: { type: Boolean },
    installRecommendedPlugins: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      margin: 20px 0;
    }

    .indexed-agents {
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
    }

    h3 {
      margin-bottom: 15px;
      font-size: 1.1em;
      color: #f0f0f0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
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
    }

    .agent-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .agent-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
    }

    .agent-info {
      flex: 1;
    }

    .agent-name {
      font-weight: bold;
      color: #f0f0f0;
    }

    .agent-description {
      font-size: 0.9em;
      color: rgba(255, 255, 255, 0.7);
      margin-top: 4px;
    }

    .index-name {
      font-size: 0.8em;
      color: rgba(255, 255, 255, 0.5);
      font-style: italic;
    }

    .install-options {
      display: flex;
      align-items: center;
      margin-bottom: 10px;
      padding: 8px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 6px;
    }

    .install-options label {
      margin-left: 8px;
    }

    .install-btn {
      padding: 4px 12px;
      background: transparent;
      border: 1px solid #4CAF50;
      color: #4CAF50;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
      transition: all 0.2s;
    }

    .install-btn:hover {
      background: rgba(76, 175, 80, 0.1);
    }

    .install-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .no-items {
      color: rgba(255, 255, 255, 0.5);
      text-align: center;
      padding: 20px;
      font-style: italic;
    }
  `;

  constructor() {
    super();
    this.indexedAgents = [];
    this.searchIndexed = '';
    this.loading = false;
    this.installRecommendedPlugins = true;
    this.scope = 'local';
    this.fetchIndexedAgents();
  }

  async fetchIndexedAgents() {
    try {
      this.loading = true;
      const response = await fetch('/index/list-indices');
      if (!response.ok) throw new Error('Failed to fetch indices');
      const result = await response.json();
      
      if (result.success) {
        // Flatten agents from all indices into a single array with index information
        this.indexedAgents = result.data.flatMap(index => 
          (index.agents || []).map(agent => ({
            ...agent,
            indexName: index.name,
            indexVersion: index.version
          }))
        );
      }
    } catch (error) {
      showNotification('error', `Error loading indexed agents: ${error.message}`);
    } finally {
      this.loading = false;
    }
  }

  async installAgent(agent) {
    try {
      this.loading = true;
      const formData = new FormData();
      formData.append('agent', JSON.stringify(agent));
      
      const response = await fetch(`/agents/${this.scope}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        // Try to get detailed error message from response
        let errorMessage = 'Failed to install agent';
        
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            // Extract the main error without the traceback
            if (typeof errorData.detail === 'string' && errorData.detail.includes('Internal server error')) {
              const mainError = errorData.detail.split('Traceback')[0].trim();
              errorMessage = mainError || errorData.detail;
            } else {
              errorMessage = errorData.detail;
            }
          }
        } catch (e) { /* Use default error message if JSON parsing fails */ }
        throw new Error(errorMessage);
      }

      // If the checkbox is checked, install recommended plugins
      if (this.installRecommendedPlugins) {
        try {
          const pluginsResponse = await fetch(`/admin/install-recommended-plugins/${agent.name}`, {
            method: 'POST'
          });
          if (!pluginsResponse.ok) {
            showNotification('warning', `Failed to install recommended plugins: ${await pluginsResponse.text()}`);
          }
        } catch (pluginError) {
          showNotification('warning', `Error installing recommended plugins: ${pluginError.message}`);
        }
      }
      
      showNotification('success', `Agent ${agent.name} installed successfully`);
      this.dispatchEvent(new CustomEvent('agent-installed', { 
        detail: agent
      }));
    } catch (error) {
      // Check for specific error messages
      if (error.message && error.message.includes('already exists')) {
        showNotification('error', `Agent ${agent.name} already exists`);
      } else {
        showNotification('error', `Error installing agent: ${error.message}`);
      }
      
    } finally { 
      this.loading = false;
    }
  }

  _render() {
    const filteredAgents = this.indexedAgents.filter(agent =>
      agent.name.toLowerCase().includes(this.searchIndexed.toLowerCase())
    );

    return html`
      <div class="indexed-agents">
        <details>
          <summary>
            <span class="material-icons">cloud_download</span>
            Available Indexed Agents
          </summary>
          <input type="text"
                 class="search-box"
                 placeholder="Search indexed agents..."
                 .value=${this.searchIndexed}
                 @input=${e => this.searchIndexed = e.target.value}>
          <div class="install-options">
            <input type="checkbox" 
                   id="install-recommended-plugins"
                   ?checked=${this.installRecommendedPlugins}
                   @change=${e => this.installRecommendedPlugins = e.target.checked}>
            <label for="install-recommended-plugins">Automatically install recommended plugins</label>
          </div>
          <div class="agent-list">
            ${filteredAgents.length ? filteredAgents.map(agent => html`
              <div class="agent-item">
                <div class="agent-info">
                  <div class="agent-name">${agent.name}</div>
                  ${agent.description ? html`
                    <div class="agent-description">${agent.description}</div>
                  ` : ''}
                  <div class="index-name">From index: ${agent.indexName}</div>
                </div>
                <button class="install-btn" 
                        @click=${() => this.installAgent(agent)}
                        ?disabled=${this.loading}>
                  Install
                </button>
              </div>
            `) : html`
              <div class="no-items">No indexed agents found</div>
            `}
          </div>
        </details>
      </div>
    `;
  }
}

customElements.define('indexed-agents', IndexedAgents);
