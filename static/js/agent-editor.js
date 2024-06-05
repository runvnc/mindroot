import { LitElement, html, css } from '/static/js/lit-core.min.js';
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
    commands: { type: Array }
  };

  static styles = [
    css`
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
    this.commands = data.commands;
  }

  async fetchAgents() {
    const response = await fetch(`/agents/${this.scope}`);
    this.agents = await response.json();
  }

  async fetchAgent() {
    if (!this.newAgent && this.name) {
      const response = await fetch(`/agents/${this.scope}/${this.name}`);
      this.agent = await response.json();
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
    }
  }

  async handleSubmit(event) {
    event.preventDefault();
    const method = this.newAgent ? 'POST' : 'PUT';
    const url = this.newAgent ? `/agents/${this.scope}` : `/agents/${this.scope}/${this.name}`;
    const formData = new FormData();
    formData.append('agent', JSON.stringify(this.agent));
    const faceref = this.shadowRoot.querySelector('input[name="faceref"]').files[0];
    const avatar = this.shadowRoot.querySelector('input[name="avatar"]').files[0];
    if (faceref) formData.append('faceref', faceref);
    if (avatar) formData.append('avatar', avatar);
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
      <textarea class="text_lg" name="instructions" .value=${this.agent.instructions || ''} @input=${this.handleInputChange}></textarea>
    </label>
  </div>
  <div>
    <label>
      Uncensored:
      <toggle-switch .checked=${this.agent.uncensored || false} @toggle-change=${(e) => this.handleInputChange({ target: { name: 'uncensored', value: e.detail.checked, type: 'checkbox' } })}></toggle-switch>
    </label>
  </div>
  <div>
    <label>
      Commands:
      ${this.commands.map(command => html`
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
