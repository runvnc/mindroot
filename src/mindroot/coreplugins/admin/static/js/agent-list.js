import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class AgentList extends BaseEl {
  static properties = {
    agents: { type: Array },
    selectedAgent: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      margin-bottom: 20px;
    }

    .agent-selector {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    select {
      flex: 1;
      padding: 8px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: #f0f0f0;
    }

    .btn {
      padding: 8px 16px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      color: #f0f0f0;
      cursor: pointer;
      transition: all 0.2s;
    }

    .btn:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .btn-secondary {
      border-color: #2196F3;
      color: #2196F3;
    }

    .btn-secondary:hover {
      background: rgba(33, 150, 243, 0.1);
    }
  `;

  async handleAgentChange(event) {
    if (event.target.value) {
      try {
        const response = await fetch(`/agents/local/${event.target.value}`);
        if (!response.ok) throw new Error('Failed to fetch agent');
        const agent = await response.json();
        this.dispatchEvent(new CustomEvent('agent-selected', {
          detail: agent
        }));
      } catch (error) {
        this.dispatchEvent(new CustomEvent('error', {
          detail: `Error loading agent: ${error.message}`
        }));
      }
    }
  }

  handleNewAgent() {
    this.dispatchEvent(new CustomEvent('new-agent'));
  }

  _render() {
    return html`
      <div class="agent-selector">
        <select @change=${this.handleAgentChange} 
                .value=${this.selectedAgent?.name || ''}>
          <option value="">Select an agent</option>
          ${this.agents.map(agent => html`
            <option value=${agent.name}>${agent.name}</option>
          `)}
        </select>
        <button class="btn btn-secondary" @click=${this.handleNewAgent}>
          New Agent
        </button>
      </div>
    `;
  }
}

customElements.define('agent-list', AgentList);
