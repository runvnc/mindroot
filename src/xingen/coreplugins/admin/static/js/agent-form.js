import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class AgentForm extends BaseEl {
  static properties = {
    agent: { type: Object },
    newAgent: { type: Boolean },
    loading: { type: Boolean },
    personas: { type: Array },
    commands: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      margin-top: 20px;
    }

    .agent-form {
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
    }

    .form-group {
      margin-bottom: 15px;
    }

    .form-group label {
      display: block;
      margin-bottom: 5px;
      color: #f0f0f0;
    }

    .required::after {
      content: " *";
      color: #e57373;
    }

    input[type="text"],
    select,
    textarea {
      width: 100%;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }

    input[type="text"]:focus,
    select:focus,
    textarea:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }

    .commands-section {
      margin-top: 20px;
    }

    .commands-category {
      margin-bottom: 15px;
    }

    .commands-category h4 {
      margin-bottom: 10px;
      color: #f0f0f0;
      font-size: 1rem;
    }

    .commands-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px;
    }

    .command-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .tooltip {
      position: relative;
      display: inline-block;
    }

    .tooltip-text {
      visibility: hidden;
      position: absolute;
      z-index: 1;
      bottom: 125%;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.9);
      color: #fff;
      text-align: center;
      padding: 5px 10px;
      border-radius: 6px;
      font-size: 0.9em;
      white-space: nowrap;
    }

    .tooltip:hover .tooltip-text {
      visibility: visible;
    }

    .btn {
      padding: 8px 16px;
      background: #2196F3;
      border: none;
      border-radius: 4px;
      color: white;
      cursor: pointer;
      font-size: 0.95rem;
      transition: all 0.2s;
    }

    .btn:hover {
      background: #1976D2;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `;

  constructor() {
    super();
    this.personas = [];
    this.commands = {};
    this.loading = false;
    this.fetchPersonas();
    this.fetchCommands();
  }

  async fetchPersonas() {
    try {
      const response = await fetch('/personas/local');
      if (!response.ok) throw new Error('Failed to fetch personas');
      this.personas = await response.json();
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error loading personas: ${error.message}`
      }));
    }
  }

  async fetchCommands() {
    try {
      const response = await fetch('/commands');
      if (!response.ok) throw new Error('Failed to fetch commands');
      const data = await response.json();
      this.commands = this.organizeCommands(data);
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error loading commands: ${error.message}`
      }));
    }
  }

  organizeCommands(commands) {
    const grouped = {};
    for (const [cmdName, cmdInfoArray] of Object.entries(commands)) {
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
      this.agent = { ...this.agent };
    } else {
      this.agent = { ...this.agent, [name]: inputValue };
    }
  }

  validateForm() {
    if (!this.agent.name?.trim()) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: 'Name is required'
      }));
      return false;
    }
    if (!this.agent.persona?.trim()) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: 'Persona is required'
      }));
      return false;
    }
    if (!this.agent.instructions?.trim()) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: 'Instructions are required'
      }));
      return false;
    }
    return true;
  }

  async handleSubmit(event) {
    event.preventDefault();
    
    if (!this.validateForm()) return;

    try {
      this.loading = true;
      const method = this.newAgent ? 'POST' : 'PUT';
      const url = this.newAgent ? '/agents/local' : `/agents/local/${this.agent.name}`;
      
      const formData = new FormData();
      const agentData = { ...this.agent };
      agentData.flags = [];
      if (this.agent.uncensored) {
        agentData.flags.push('uncensored');
      }
      
      formData.append('agent', JSON.stringify(agentData));
      
      const response = await fetch(url, {
        method,
        body: formData
      });

      if (!response.ok) throw new Error('Failed to save agent');
      
      this.dispatchEvent(new CustomEvent('agent-saved', {
        detail: this.agent
      }));
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error saving agent: ${error.message}`
      }));
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
      <form class="agent-form" @submit=${this.handleSubmit}>
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
    `;
  }
}

customElements.define('agent-form', AgentForm);
