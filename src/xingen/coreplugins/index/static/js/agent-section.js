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
      padding: 20px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      background: rgba(20, 20, 35, 0.6);
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .content-section h3 {
      margin: 0 0 20px 0;
      font-size: 1.2em;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.8rem;
      padding-bottom: 15px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .split-view {
      display: flex;
      gap: 25px;
      margin-top: 15px;
      min-height: 400px;
      max-height: 600px;
    }

    .available-items, .selected-items {
      flex: 1;
      background: rgba(30, 30, 50, 0.6);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .available-items h4, .selected-items h4 {
      margin: 0 0 15px 0;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      color: #fff;
      font-size: 1.1rem;
      font-weight: 500;
      flex-shrink: 0;
    }

    .search-box {
      width: 100%;
      padding: 10px 15px;
      margin-bottom: 15px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      color: #fff;
      font-size: 0.95rem;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }

    .search-box:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
      box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.05);
    }

    .item-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      overflow-y: auto;
      flex-grow: 1;
      padding-right: 8px;
    }

    .item-entry {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 15px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      transition: all 0.2s ease;
    }

    .item-entry:hover {
      background: rgba(255, 255, 255, 0.06);
      border-color: rgba(255, 255, 255, 0.1);
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .item-entry .name {
      flex: 1;
      color: #fff;
      font-weight: 500;
    }

    .item-entry .version {
      color: rgba(255, 255, 255, 0.6);
      font-size: 0.9em;
      margin: 0 15px;
      font-family: 'SF Mono', 'Consolas', monospace;
      background: rgba(255, 255, 255, 0.05);
      padding: 2px 6px;
      border-radius: 4px;
    }

    .item-entry button {
      padding: 6px 14px;
      background: transparent;
      border: 1px solid currentColor;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9em;
      transition: all 0.2s ease;
      font-weight: 500;
    }

    .item-entry button.add {
      color: #4CAF50;
    }

    .item-entry button.add:hover {
      background: rgba(76, 175, 80, 0.1);
      transform: translateY(-1px);
    }

    .item-entry button.remove {
      color: #f44336;
    }

    .item-entry button.remove:hover {
      background: rgba(244, 67, 54, 0.1);
      transform: translateY(-1px);
    }

    .no-items {
      color: rgba(255, 255, 255, 0.5);
      text-align: center;
      padding: 30px;
      font-style: italic;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 8px;
      border: 1px dashed rgba(255, 255, 255, 0.1);
    }

    /* Scrollbar styling */
    .item-list::-webkit-scrollbar {
      width: 8px;
    }

    .item-list::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
    }

    .item-list::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 4px;
    }

    .item-list::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.2);
    }
  `;
  constructor() {
    super();
    this.searchAgents = '';
  }

  async addAgent(agent) {
    try {
      const agentEntry = {
        name: agent.name,
        version: agent.version || '1.0.0',
        description: agent.description || '',
        required_commands: agent.required_commands || [],
        required_services: agent.required_services || []
      };

      const response = await fetch(`/index/add-agent/${this.selectedIndex.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentEntry)
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
      alert('Failed to add agent: ' + (error.message || 'Unknown error'));
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
                    <span class="version">${agent.version || '1.0.0'}</span>
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
                  <span class="version">${agent.version || '1.0.0'}</span>
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
