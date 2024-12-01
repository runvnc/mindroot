import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class AgentSection extends BaseEl {
  static properties = {
    selectedIndex: { type: Object },
    availableAgents: { type: Array },
    loading: { type: Boolean },
    searchAgents: { type: String }
  }

  static styles = css`
    :host {
      display: block;
      margin: 15px 0;
    }

    .content-section {
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
  `;

  constructor() {
    super();
    this.searchAgents = '';
  }

  async addAgent(agent) {
    try {
      const response = await fetch(`/index/add-agent/${this.selectedIndex.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: agent.name,
          version: agent.version || '0.0.1',
          description: agent.description || ''
        })
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('agent-added', {
          detail: agent
        }));
      } else {
        alert(`Failed to add agent: ${result.message}`);
      }
    } catch (error) {
      console.error('Error adding agent:', error);
      alert('Failed to add agent');
    }
  }

  async removeAgent(agent) {
    try {
      const response = await fetch(`/index/remove-agent/${this.selectedIndex.name}/${agent.name}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('agent-removed', {
          detail: agent
        }));
      } else {
        alert(`Failed to remove agent: ${result.message}`);
      }
    } catch (error) {
      console.error('Error removing agent:', error);
      alert('Failed to remove agent');
    }
  }

  isAgentInIndex(agent) {
    return this.selectedIndex?.agents?.some(a => a.name === agent.name) || false;
  }

  _render() {
    if (!this.selectedIndex) return html``;

    return html`
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
    `;
  }
}

customElements.define('agent-section', AgentSection);
