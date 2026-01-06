import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './agent-form.js';
import './indexed-agents.js';
import './github-import.js';
import './missing-commands.js';

class AgentEditor extends BaseEl {
  static properties = {
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
    this.attachShadow({ mode: 'open' });
    this.loading = false;
    this.errorMessage = '';
    this.importStatus = '';
  }

  handleAgentSaved(e) {
    this.importStatus = 'Agent saved successfully';
    
    setTimeout(() => {
      this.importStatus = '';
    }, 3000);
  }

  handleAgentInstalled(e) {
    this.importStatus = `Successfully installed ${e.detail.name}`;
    
    // Notify the agent-form to refresh its agent list
    const agentForm = this.shadowRoot.querySelector('agent-form');
    if (agentForm) {
      agentForm.fetchAgents();
    }
    
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

        <indexed-agents
          @agent-installed=${this.handleAgentInstalled}
          @error=${this.handleError}>
        </indexed-agents>

        <agent-form
          @agent-saved=${this.handleAgentSaved}
          @error=${this.handleError}>
        </agent-form>

        <github-import
          @agent-installed=${this.handleAgentInstalled}
          @error=${this.handleError}>
        </github-import>

      </div>
    `;
  }
}

customElements.define('agent-editor', AgentEditor);
