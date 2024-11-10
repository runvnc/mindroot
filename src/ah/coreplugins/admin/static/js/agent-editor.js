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
    githubImportStatus: { type: String }
  };

  static styles = [
    css`
      .import-status {
        margin-top: 10px;
        font-weight: bold;
      }
      .import-status.success {
        color: green;
      }
      .import-status.error {
        color: red;
      }
      .github-import {
        margin-top: 10px;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
      }
      .github-import input {
        margin-right: 10px;
        padding: 4px;
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
    this.fetchPersonas();
    this.fetchCommands();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchAgents();
  }

  async fetchPersonas() {
    const response = await fetch(`/personas/${this.scope}`);
    this.personas = await response.json();
  }

  async fetchCommands() {
    const response = await fetch(`/commands`);
    const data = await response.json();
    this.commands = data;
  }

  async fetchAgents() {
    const response = await fetch(`/agents/${this.scope}`);
    this.agents = await response.json();
  }

  async fetchAgent() {
    if (!this.newAgent && this.name) {
      const response = await fetch(`/agents/${this.scope}/${this.name}`);
      this.agent = await response.json();
      this.agent.uncensored = this.agent.flags.includes('uncensored')
      console.log('agent', this.agent)
    } else {
      this.agent = {};
    }
  }

  handleScopeChange(event) {
    this.scope = event.target.value;
    this.fetchAgents();
  }

  handleAgentChange(event) {
    this.name = event.target.value;
    this.newAgent = false;
    this.fetchAgent();
  }

  handleNewAgent() {
    this.newAgent = true;
    this.agent = {};
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
      console.log("agent updated:", {inputValue, name, newAgent: this.agent})
    }
  }

  async handleSubmit(event) {
    event.preventDefault();
    const method = this.newAgent ? 'POST' : 'PUT';
    const url = this.newAgent ? `/agents/${this.scope}` : `/agents/${this.scope}/${this.name}`;
    const formData = new FormData();
    this.agent.flags = [] 
    if (this.agent.uncensored) { 
      this.agent.flags.push('uncensored')
    }
    formData.append('agent', JSON.stringify(this.agent));
    const response = await fetch(url, {
      method,
      body: formData
    });
    if (response.ok) {
      alert('Agent saved successfully');
      this.newAgent = false;
      this.fetchAgents();
    } else {
      alert('Failed to save agent');
    }
  }

  handleFileChange(event) {
    const { name, files } = event.target;
    this.agent = { ...this.agent, [name]: files[0] };
  }

  async handleScanAndImport() {
    const directory = prompt("Enter the directory path to scan for agents:");
    if (!directory) return;

    try {
      const response = await fetch('/scan-and-import-agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ directory, scope: this.scope })
      });

      const result = await response.json();
      if (result.success) {
        this.importStatus = `Success: Imported ${result.imported_agents.length} agents`;
        this.fetchAgents(); // Refresh the agent list
      } else {
        this.importStatus = `Error: ${result.message}`;
      }
    } catch (error) {
      this.importStatus = `Error: ${error.message}`;
    }

    // Clear the status message after 5 seconds
    setTimeout(() => {
      this.importStatus = '';
    }, 5000);
  }

  async handleGitHubImport() {
    const repoPath = this.shadowRoot.querySelector('#githubRepo').value;
    const tag = this.shadowRoot.querySelector('#githubTag').value;

    if (!repoPath) {
      this.githubImportStatus = 'Error: Repository path is required';
      return;
    }

    try {
      const response = await fetch('/import-github-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: repoPath,
          scope: this.scope,
          tag: tag || null
        })
      });

      const result = await response.json();
      if (response.ok) {
        this.githubImportStatus = `Success: ${result.message}`;
        this.fetchAgents(); // Refresh the agent list
      } else {
        this.githubImportStatus = `Error: ${result.detail || result.message}`;
      }
    } catch (error) {
      this.githubImportStatus = `Error: ${error.message}`;
    }

    // Clear the status message after 5 seconds
    setTimeout(() => {
      this.githubImportStatus = '';
    }, 5000);
  }

  _render() {
    return html`
      <div>
        <label>
          <input type="radio" name="scope" value="local" .checked=${this.scope === 'local'} @change=${this.handleScopeChange} /> Local
        </label>
        <label>
          <input type="radio" name="scope" value="shared" .checked=${this.scope === 'shared'} @change=${this.handleScopeChange} /> Shared
        </label>
        <select @change=${this.handleAgentChange} .value=${this.name || ''} ?disabled=${this.newAgent}>
          <option value="">Select an agent</option>
          ${this.agents.map(agent => html`<option value="${agent.name}">${agent.name}</option>`) }
        </select>
        <button @click=${this.handleNewAgent}>New Agent</button>
        <button @click=${this.handleScanAndImport}>Scan and Import Agents</button>
        ${this.importStatus ? html`<div class="import-status ${this.importStatus.startsWith('Success') ? 'success' : 'error'}">${this.importStatus}</div>` : ''}
        
        <!-- GitHub Import Section -->
        <div class="github-import">
          <h3>Import from GitHub</h3>
          <input type="text" id="githubRepo" placeholder="owner/repository" />
          <input type="text" id="githubTag" placeholder="tag (optional)" />
          <button @click=${this.handleGitHubImport}>Import from GitHub</button>
          ${this.githubImportStatus ? html`<div class="import-status ${this.githubImportStatus.startsWith('Success') ? 'success' : 'error'}">${this.githubImportStatus}</div>` : ''}
        </div>
      </div>
      <form @submit=${this.handleSubmit} class="agent">
  <div>
    <label>
      Name:
      <input class="text_inp" type="text" name="name" .value=${this.agent.name || ''} @input=${this.handleInputChange} />
    </label>
  </div>
  <div>
    <label>
      Persona:
      <select name="persona" .value=${this.agent.persona || ''} @input=${this.handleInputChange}>
        <option value="">Select a persona</option>
        ${this.personas.map(persona => html`<option value="${persona.name}">${persona.name}</option>`) }
      </select>
    </label>
  </div>
  <div>
    <label>
      Instructions:
      <textarea class="text_lg" name="instructions" rows="20" .value=${this.agent.instructions || ''} @input=${this.handleInputChange}></textarea>
    </label>
  </div>
  <div>
    <label>
      Uncensored:
      <toggle-switch .checked=${this.agent.uncensored || false} 
                     @toggle-change=${(e) => {
                       console.log(e);
                       this.handleInputChange({ 
                         target: { name: 'uncensored', 
                           checked: e.detail.checked, 
                           type: 'checkbox' } 
                        })
                      }}></toggle-switch>
    </label>
  </div>
  <div>
    <label>
      Commands:
      ${this.commands && this.commands.map(command => html`
        <label>
          <input type="checkbox" name="commands" value="${command}" .checked=${this.agent.commands && this.agent.commands.includes(command)} @change=${this.handleInputChange} /> ${command}
        </label>
      `)}
    </label>
  </div>
  
  
  <button class="btn" type="submit">Save</button>
</form>
    `;
  }
}

customElements.define('agent-editor', AgentEditor);
