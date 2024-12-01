import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class AgentEditor extends BaseEl {
  static properties = {
    agent: { type: Object },
    scope: { type: String },
    name: { type: String },
    agents: { type: Array },
    newAgent: { type: Boolean },
    personas: { type: Array },
    commands: { type: Array },
    importStatus: { type: String },
    githubImportStatus: { type: String },
    loading: { type: Boolean },
    errorMessage: { type: String }
  };

  static styles = [
    css`
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
      .required::after {
        content: " *";
        color: #e57373;
      }
      .action-buttons {
        display: flex;
        gap: 10px;
        margin-top: 10px;
      }
    `
  ];

  constructor() {
    super();
    this.agent = {};
    this.agents = [];
    this.personas = [];
    this.commands = [];
    this.scope = 'local';
    this.newAgent = false;
    this.importStatus = '';
    this.githubImportStatus = '';
    this.loading = false;
    this.errorMessage = '';
    this.fetchPersonas();
    this.fetchCommands();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchAgents();
  }

  async fetchPersonas() {
    try {
      this.loading = true;
      const response = await fetch(`/personas/${this.scope}`);
      if (!response.ok) throw new Error('Failed to fetch personas');
      this.personas = await response.json();
    } catch (error) {
      this.errorMessage = `Error loading personas: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async fetchCommands() {
    try {
      this.loading = true;
      const response = await fetch(`/commands`);
      if (!response.ok) throw new Error('Failed to fetch commands');
      const data = await response.json();
      this.commands = this.organizeCommands(data);
    } catch (error) {
      this.errorMessage = `Error loading commands: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  organizeCommands(commands) {
    // Group commands by provider
    const grouped = {};
    for (const [cmdName, cmdInfoArray] of Object.entries(commands)) {
      // Take the first implementation's provider as the grouping key
      // This assumes all implementations of a command come from the same provider
      const cmdInfo = cmdInfoArray[0];
      const provider = cmdInfo.provider || 'Other';
      if (!grouped[provider]) {
        grouped[provider] = [];
      }
      grouped[provider].push({
        name: cmdName,
        docstring: cmdInfo.docstring,
        flags: cmdInfo.flags
      });
    }
    return grouped;
  }

  async fetchAgents() {
    try {
      this.loading = true;
      const response = await fetch(`/agents/${this.scope}`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      this.agents = await response.json();
    } catch (error) {
      this.errorMessage = `Error loading agents: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  async fetchAgent() {
    if (!this.newAgent && this.name) {
      try {
        this.loading = true;
        const response = await fetch(`/agents/${this.scope}/${this.name}`);
        if (!response.ok) throw new Error('Failed to fetch agent');
        this.agent = await response.json();
        this.agent.uncensored = this.agent.flags?.includes('uncensored');
      } catch (error) {
        this.errorMessage = `Error loading agent: ${error.message}`;
      } finally {
        this.loading = false;
      }
    } else {
      this.agent = {};
    }
  }

  async addToIndex() {
    if (!this.agent.name) {
      this.errorMessage = 'Please save the agent first';
      return;
    }

    try {
      this.loading = true;
      // Get the index name from user
      const indexName = prompt('Enter the name of the index to add this agent to:');
      if (!indexName) return;

      const response = await fetch(`/index/add-agent/${indexName}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.agent.name,
          version: this.agent.version || '0.0.1',
          description: this.agent.description || ''
        })
      });

      const result = await response.json();
      if (result.success) {
        this.importStatus = `Successfully added ${this.agent.name} to index ${indexName}`;
      } else {
        throw new Error(result.message || 'Failed to add agent to index');
      }
    } catch (error) {
      this.errorMessage = `Error adding agent to index: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  validateForm() {
    if (!this.agent.name?.trim()) {
      this.errorMessage = 'Name is required';
      return false;
    }
    if (!this.agent.persona?.trim()) {
      this.errorMessage = 'Persona is required';
      return false;
    }
    if (!this.agent.instructions?.trim()) {
      this.errorMessage = 'Instructions are required';
      return false;
    }
    return true;
  }

  handleScopeChange(event) {
    this.scope = event.target.value;
    this.fetchAgents();
  }

  handleAgentChange(event) {
    if (confirm('Loading a different agent will discard any unsaved changes. Continue?')) {
      this.name = event.target.value;
      this.newAgent = false;
      this.fetchAgent();
    }
  }

  handleNewAgent() {
    if (confirm('Creating a new agent will discard any unsaved changes. Continue?')) {
      this.newAgent = true;
      this.agent = {};
    }
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    
    if (name === 'commands') {
      if (!Array.isArray(this.agent.commands)) {
        this.agent.commands = [];
      }
      if (checked) {
        this.agent.commands.push(value);
      } else {
        this.agent.commands = this.agent.commands.filter(command => command !== value);
      }
    } else {
      this.agent = { ...this.agent, [name]: inputValue };
    }
    this.errorMessage = '';
  }

  async handleSubmit(event) {
    event.preventDefault();
    
    if (!this.validateForm()) return;

    try {
      this.loading = true;
      const method = this.newAgent ? 'POST' : 'PUT';
      const url = this.newAgent ? `/agents/${this.scope}` : `/agents/${this.scope}/${this.name}`;
      
      const formData = new FormData();
      this.agent.flags = [];
      if (this.agent.uncensored) {
        this.agent.flags.push('uncensored');
      }
      
      formData.append('agent', JSON.stringify(this.agent));
      
      const response = await fetch(url, {
        method,
        body: formData
      });

      if (!response.ok) throw new Error('Failed to save agent');
      
      this.importStatus = 'Agent saved successfully';
      this.newAgent = false;
      await this.fetchAgents();
      
      setTimeout(() => {
        this.importStatus = '';
      }, 3000);
    } catch (error) {
      this.errorMessage = `Error saving agent: ${error.message}`;
    } finally {
      this.loading = false;
    }
  }

  renderCommands() {
    return Object.entries(this.commands).map(([provider, commands]) => html`
      <div class="commands-category">
        <h4>${provider}</h4>
        <div class="commands-grid">
          ${commands.map(command => html`
            <div class="command-item">
              <input type="checkbox" 
                     name="commands" 
                     value="${command.name}" 
                     .checked=${this.agent.commands?.includes(command.name)}
                     @change=${this.handleInputChange} />
              <div class="tooltip">
                <span class="command-name">${command.name}</span>
                ${command.docstring ? html`
                  <span class="tooltip-text">${command.docstring}</span>
                ` : ''}
              </div>
            </div>
          `)}
        </div>
      </div>
    `);
  }

  _render() {
    return html`
      <div class="agent-editor ${this.loading ? 'loading' : ''}">
        ${this.errorMessage ? html`
          <div class="error-message">${this.errorMessage}</div>
        ` : ''}
        
        <div class="scope-selector">
          <label>
            <input type="radio" name="scope" value="local" 
                   .checked=${this.scope === 'local'} 
                   @change=${this.handleScopeChange} /> Local
          </label>
          <label>
            <input type="radio" name="scope" value="shared" 
                   .checked=${this.scope === 'shared'} 
                   @change=${this.handleScopeChange} /> Shared
          </label>
        </div>

        <div class="agent-selector">
          <select @change=${this.handleAgentChange} 
                  .value=${this.name || ''} 
                  ?disabled=${this.newAgent}>
            <option value="">Select an agent</option>
            ${this.agents.map(agent => html`
              <option value="${agent.name}">${agent.name}</option>
            `)}
          </select>
          <div class="action-buttons">
            <button class="btn btn-secondary" @click=${this.handleNewAgent}>New Agent</button>
            <button class="btn btn-secondary" @click=${this.handleScanAndImport}>
              Scan and Import Agents
            </button>
            ${!this.newAgent && this.agent.name ? html`
              <button class="btn btn-primary" @click=${this.addToIndex}>Add to Index</button>
            ` : ''}
          </div>
        </div>

        ${this.importStatus ? html`
          <div class="status-message ${this.importStatus.startsWith('Success') ? 'success' : 'error'}">
            ${this.importStatus}
          </div>
        ` : ''}

        <div class="github-import">
          <h3>Import from GitHub</h3>
          <div class="github-import-form">
            <input type="text" id="githubRepo" 
                   placeholder="owner/repository" 
                   class="tooltip">
            <input type="text" id="githubTag" 
                   placeholder="tag (optional)" 
                   class="tooltip">
            <button class="btn btn-secondary" 
                    @click=${this.handleGitHubImport}>Import from GitHub</button>
          </div>
          ${this.githubImportStatus ? html`
            <div class="status-message ${this.githubImportStatus.startsWith('Success') ? 'success' : 'error'}">
              ${this.githubImportStatus}
            </div>
          ` : ''}
        </div>

        <form @submit=${this.handleSubmit} class="agent-form">
          <div class="form-group">
            <label class="required">Name:</label>
            <input type="text" name="name" 
                   .value=${this.agent.name || ''} 
                   @input=${this.handleInputChange}>
          </div>

          <div class="form-group">
            <label class="required">Persona:</label>
            <select name="persona" 
                    .value=${this.agent.persona || ''} 
                    @input=${this.handleInputChange}>
              <option value="">Select a persona</option>
              ${this.personas.map(persona => html`
                <option value="${persona.name}">${persona.name}</option>
              `)}
            </select>
          </div>

          <div class="form-group">
            <label class="required">Instructions:</label>
            <textarea name="instructions" 
                      rows="20" 
                      .value=${this.agent.instructions || ''} 
                      @input=${this.handleInputChange}></textarea>
          </div>

          <div class="form-group">
            <label>
              Uncensored:
              <toggle-switch 
                .checked=${this.agent.uncensored || false}
                @toggle-change=${(e) => {
                  this.handleInputChange({
                    target: {
                      name: 'uncensored',
                      checked: e.detail.checked,
                      type: 'checkbox'
                    }
                  });
                }}></toggle-switch>
            </label>
          </div>

          <div class="form-group commands-section">
            <label>Commands:</label>
            ${this.renderCommands()}
          </div>

          <button class="btn" type="submit" ?disabled=${this.loading}>
            ${this.loading ? 'Saving...' : 'Save'}
          </button>
        </form>
      </div>
    `;
  }
}

customElements.define('agent-editor', AgentEditor);
