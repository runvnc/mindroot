import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './agent-form.js';
import './agent-list.js';
import './indexed-agents.js';
import './github-import.js';
import './missing-commands.js';

class AgentEditor extends BaseEl {
  static properties = {
    agent: { type: Object, reflect: true },
    name: { type: String, reflect: true },
    agents: { type: Array, reflect: true },
    newAgent: { type: Boolean, reflect: true},
    loading: { type: Boolean, reflect: true },
    errorMessage: { type: String, reflect: true },
    importStatus: { type: String, reflect: true }
  };

  static styles = css`
    :host {
      display: block;
    }
    .loading {
      opacity: 0.7;
      pointer-events: none;
    }
    .error-message {
      color: #e57373;
      margin: 1rem 0;
      padding: 0.75rem;
      border: 1px solid rgba(244, 67, 54, 0.2);
      border-radius: 4px;
      background: rgba(244, 67, 54, 0.1);
    }
    .status-message {
      margin: 1rem 0;
      padding: 0.75rem;
      border-radius: 4px;
    }
    .status-message.success {
      color: #81c784;
      border: 1px solid rgba(129, 199, 132, 0.2);
      background: rgba(129, 199, 132, 0.1);
    }
    .status-message.error {
      color: #e57373;
      border: 1px solid rgba(244, 67, 54, 0.2);
      background: rgba(244, 67, 54, 0.1);
    }
  `;

  constructor() {
    super();
    this.agent = {};
    this.agents = [];
    this.attachShadow({ mode: 'open' });
    this.newAgent = false;
    this.loading = false;
    this.errorMessage = '';
    this.importStatus = '';
    this.fetchAgents();
  }

  async fetchAgents() {
    try {
      this.loading = true;
      const response = await fetch('/agents/local');
      if (!response.ok) throw new Error('Failed to fetch agents');
      this.agents = await response.json();
      console.log({agents: this.agents})
    } catch (error) {
      this.errorMessage = `Error loading agents: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  handleAgentSelected(e) {
    this.agent = e.detail;
    this.newAgent = false;
    this.name = e.detail.name;
  }

  handleNewAgent() {
    this.agent = {};
    this.newAgent = true;
    this.name = '';
  }

  handleAgentSaved(e) {
    this.importStatus = 'Agent saved successfully';
    this.newAgent = false;
    
    // Just update the current agent with saved data without refreshing the list
    this.agent = {...e.detail};
    
    setTimeout(() => {
      this.importStatus = '';
    }, 3000);
  }

  handleAgentInstalled(e) {
    this.importStatus = `Successfully installed ${e.detail.name}`;
    this.fetchAgents();
    setTimeout(() => {
      this.importStatus = '';
    }, 3000);
  }

  handleError(e) {
    this.errorMessage = e.detail;
  }

  _render() {
    return html`
      <div class="agent-editor ${this.loading ? 'loading' : ''}">
        ${this.errorMessage ? html`
          <div class="error-message">${this.errorMessage}</div>
        ` : ''}
        
        ${this.importStatus ? html`
          <div class="status-message ${this.importStatus.startsWith('Success') ? 'success' : 'error'}">
            ${this.importStatus}
          </div>
        ` : ''}

        <agent-list
          .agents=${this.agents}
          .selectedAgent=${this.agent}
          @agent-selected=${this.handleAgentSelected}
          @new-agent=${this.handleNewAgent}>
        </agent-list>

        ${(true || this.newAgent || this.agent.name) ? html`
          <agent-form
            .agent=${this.agent}
            .newAgent=${this.newAgent}
            @agent-saved=${this.handleAgentSaved}
            @error=${this.handleError}>
          </agent-form>
        ` : ''}

        <indexed-agents
          @agent-installed=${this.handleAgentInstalled}
          @error=${this.handleError}>
        </indexed-agents>

        <github-import
          @agent-installed=${this.handleAgentInstalled}
          @error=${this.handleError}>
        </github-import>


      </div>
    `;
  }
}

customElements.define('agent-editor', AgentEditor);
