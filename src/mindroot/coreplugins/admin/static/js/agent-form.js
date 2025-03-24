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

    summary::before {
      content: "\u25b6";
      display: inline-block;
      margin-right: 5px;
      transition: transform 0.2s;
    }

    details[open] > summary::before { transform: rotate(90deg); }

    details > * :not(summary) {
      user-select: none;
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

    textarea {
      min-height: 60vh;
    }

    textarea::-webkit-scrollbar {
      width: 8px;  /* Medium-thin width */
    }

    textarea::-webkit-scrollbar-track {
      background: #222;  /* Dark background */
    }

    textarea::-webkit-scrollbar-thumb {
      background: #666;  /* Medium gray scrollbar handle */
      border-radius: 4px;
    }

    textarea::-webkit-scrollbar-thumb:hover {
      background: #999;  /* Lighter on hover */
    }

    textarea {
      scrollbar-width: thin;
      scrollbar-color: #666 #222;
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
      margin-bottom: 20px;
      background: rgba(255, 255, 255, 0.02);
      border-radius: 8px;
      padding: 15px;
    }

    .commands-category h4 {
      margin-bottom: 15px;
      color: #f0f0f0;
      font-size: 1.1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 8px;
    }

    .commands-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 12px;
    }

    .command-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .command-item:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .command-info {
      flex: 1;
      margin-right: 12px;
      position: relative;
    }

    .command-name {
      color: #f0f0f0;
      font-weight: 500;
    }

    .tooltip-text {
      visibility: hidden;
      position: absolute;
      z-index: 1;
      left: 0;
      top: 100%;
      margin-top: 10px;
      width: 250px;
      background-color: rgba(0, 0, 0, 0.9);
      color: #fff;
      text-align: left;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.9em;
      line-height: 1.4;
      white-space: normal;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .command-info:hover .tooltip-text {
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
    this.attachShadow({mode: 'open'});
    this.personas = [];
    this.commands = {};
    this.loading = false;
    this.plugins = [];
    this.providerMapping = {}; // Map display names to module names
    this.agent = {
      commands: [],
      name: '',
      preferred_providers: [],
      thinking_level: 'off', // Default to medium
      persona: '',
      required_plugins: []
    };
    this.fetchPersonas();
    this.fetchCommands();
    this.fetchPlugins();
  }

  updated(changedProperties) {
    console.log('Updated with changes:', changedProperties);
    super.updated(changedProperties);
    if (changedProperties.has('agent')) {
      console.log('Agent updated:', this.agent);
      // Force select element to update
      const select = this.shadowRoot.querySelector('select[name="persona"]');
      if (select && this.agent.persona) {
        select.value = this.agent.persona;
      }
    }
  }

  // Fetch available personas
  async fetchPersonas() {
    try {
      const response = await fetch('/personas/local');
      if (!response.ok) throw new Error('Failed to fetch personas');
      this.personas = await response.json();
      console.log('Fetched personas:', this.personas);
      console.log('Current agent persona:', this.agent.persona);
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error loading personas: ${error.message}`
      }));
    }
  }

  async fetchPlugins() {
    try {
      const response = await fetch('/plugin-manager/get-all-plugins');
      if (!response.ok) throw new Error('Failed to fetch plugins');
      const result = await response.json();
      this.plugins = result.data.filter(plugin => plugin.enabled);
      console.log('Fetched plugins:', this.plugins);
      
      // Add category (module name) for each plugin if available
      for (const plugin of this.plugins) {
        let name = plugin.name;
        if (plugin.source_path) {
           name = plugin.source_path.split('/').filter(Boolean).pop();
        } 
        const uniqueId = name.replace(/[^a-zA-Z0-9]/g, '_');
        name = uniqueId;
        plugin.name = name
        plugin._uniqueId = uniqueId;
        plugin._id = uniqueId
      }
      
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error loading plugins: ${error.message}`
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
        this.plugins.push(provider)
      }
      grouped[provider].push({
        name: cmdName,
        provider,
        providerName: provider,
        docstring: cmdInfo.docstring,
        flags: cmdInfo.flags,
        uniqueId: `${cmdName}_${provider}`.replace(/[^a-zA-Z0-9]/g, '_')
      });
      
      this.providerMapping[provider] = provider;
    }
    return grouped;
  }

  handleInputChange(event) {  
    const { name, value, type, checked } = event.target;
    
    if (name === 'commands') {
      if (!Array.isArray(this.agent.commands)) {
        this.agent.commands = [];
      }
      if (checked) {
        this.agent.commands.push(value);
      } else {
        this.agent.commands = this.agent.commands.filter(command => command !== value);
      }

      // Update the entire agent object WITHOUT overwriting commands
      this.agent = { ...this.agent };
      return;
    }
    
    // Handle required_plugins similar to commands
    if (name === 'required_plugins') {
      if (!Array.isArray(this.agent.required_plugins)) {
        this.agent.required_plugins = [];
      }
      if (checked) {
        this.agent.required_plugins.push(value);
      } else {
        this.agent.required_plugins = this.agent.required_plugins.filter(plugin => plugin !== value);
      }
      this.agent = { ...this.agent };
      return;
    }
    
    // Handle all other inputs
    const inputValue = type === 'checkbox' ? checked : value;
    this.agent = { ...this.agent, [name]: inputValue };
  }

  handlePreferredProviderChange(e) {
    const { value, checked, id } = e.detail || e.target;
    console.log(`Preferred provider change: ID=${id || 'unknown'} Value=${value}, Checked=${checked}`);
    
    // Ensure preferred_providers is always an array
    if (!Array.isArray(this.agent.preferred_providers)) {
      this.agent.preferred_providers = [];
    }
    
    let preferred_providers = [...this.agent.preferred_providers];
    
    if (checked) {
      if (!preferred_providers.includes(id)) {
        preferred_providers.push(id);
        console.log(`Added ${id} to preferred_providers: ${preferred_providers.join(', ')}`);
      }
    } else {
      const index = preferred_providers.indexOf(id);
      if (index !== -1) preferred_providers.splice(index, 1);
      console.log(`Removed ${id} from preferred_providers: ${preferred_providers.join(', ')}`);
    }
    
    this.agent = { ...this.agent, preferred_providers };
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

  async handleSubmit(event) {  // Complete replacement of method
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
        // Make sure flags is an array
        if (!Array.isArray(agentData.flags)) {
          agentData.flags = [];
        }
        agentData.flags.push('uncensored');
      }
      
      formData.append('agent', JSON.stringify(agentData));
      
      const response = await fetch(url, {
        method,
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to save agent');
      }

      // Get the saved agent data from response and update local state
      const savedAgent = await response.json();
      // Update our local agent with the server data
      this.agent = savedAgent;

      this.dispatchEvent(new CustomEvent('agent-saved', {
        detail: savedAgent
      }));
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error saving agent: ${error.message}`
      }));
    } finally {
      this.loading = false;
    }
  }

  renderRequiredPlugins() {
    return
    // Ensure required_plugins is always an array
    if (!this.agent.required_plugins) {
      this.agent.required_plugins = [];
    } else if (!Array.isArray(this.agent.required_plugins)) {
      this.agent.required_plugins = [this.agent.required_plugins];
    }
    
    if (!this.plugins || this.plugins.length === 0) {
      // Fetch plugins if not already loaded
      if (!this.pluginsFetched) {
        this.pluginsFetched = true;
        this.fetchPlugins();
      }
      return html`<div>Loading plugins...</div>`;
    }
    
    return html`
      <div class="commands-category">
        <h4>Required Plugins</h4>
        <div class="commands-grid">
          ${this.plugins.map(plugin => {
            // Use provider name (module name) as the value
            // Create a unique ID for each toggle
            const providerName = plugin.category || plugin.name;
            const toggleId = `req_${plugin._uniqueId}`;
            
            console.log(`Rendering required plugin: ${plugin.name}, providerName: ${providerName}, toggleId: ${toggleId}`);
            
            return html`
            <div class="command-item">
              <div class="command-info">
                <div class="command-name">${plugin.name}</div>
              </div>
              <toggle-switch 
                .checked=${this.agent.required_plugins?.includes(providerName) || false}
                id="${toggleId}"
                @toggle-change=${(e) => this.handleInputChange({ 
                  target: { 
                    plugin: plugin,
                    name: 'required_plugins', 
                    value: providerName,
                    type: 'checkbox', 
                    checked: e.detail.checked 
                  } 
                })}>
              </toggle-switch>
            </div>
          `;})}
        </div>
      </div>
    `;
  }

  renderCommands() {
    return Object.entries(this.commands).map(([provider, commands]) => html`
      <div class="commands-category">
        <details>
          <summary>${provider}</summary>
          <div class="commands-grid">
            ${commands.map(command => html`
              <div class="command-item">
                <div class="command-info">
                  <div class="command-name">${command.name}</div>
                  ${command.docstring ? html`
                    <div class="tooltip-text">${command.docstring}</div>
                  ` : ''}
                </div>
                <toggle-switch 
                  .checked=${this.agent.commands?.includes(command.name) || false}
                  @toggle-change=${(e) => this.handleInputChange({ 
                    target: {
                      name: 'commands', 
                      value: command.name, 
                      type: 'checkbox',
                      checked: e.detail.checked 
                    }
                  })}>
                </toggle-switch>
              </div>
            `)}
          </div>
        </details>
      </div>
    `);
  }

  renderPreferredProviders() {
    // Ensure preferred_providers is always an array
    if (!Array.isArray(this.agent.preferred_providers)) {
      this.agent.preferred_providers = [];
    }
    console.log('Preferred providers:', this.agent.preferred_providers);
    return html`
      <div class="commands-category">
        <h4>Preferred Providers</h4>
        <div class="commands-grid">
          ${this.plugins.map(plugin => {
            // Use provider name (module name) as the value
            // Create a unique ID for each toggle
            const toggleId = `pref_${plugin.name}`
            console.log(`Rendering preferred provider for plugin: ${plugin.name}`)
            return html`
            <div class="command-item" data-provider="${plugin.name}">
              <div class="command-info">
                <div class="command-name">${plugin.name}</div>
              </div>
              <toggle-switch 
                .checked=${this.agent.preferred_providers?.includes(plugin.name) || false}
                id="${toggleId}"
                @toggle-change=${(e) => this.handlePreferredProviderChange({ 
                  detail: {
                    plugin: plugin.name,
                    value: plugin.name, 
                    id: plugin.name,
                    checked: e.detail.checked 
                  } 
                })}>
              </toggle-switch>
            </div>
          `;})}
        </div>
      </div>
    `;
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
                  value=${this.agent.persona || ''}
                  @change=${this.handleInputChange}>
            <option value="">Select a persona</option>
            ${this.personas.map(persona => html`
              <option value="${persona.name}" ?selected=${persona.name === this.agent.persona}>${persona.name}</option>
            `)}
          </select>
        </div>

        <div class="form-group">
          <label class="required">Instructions:</label>
          <textarea name="instructions" 
                    .value=${this.agent.instructions || ''} 
                    @input=${this.handleInputChange}></textarea>
        </div>

        <div class="form-group">
          <label>
            Uncensored:
            <toggle-switch 
              .checked=${this.agent.uncensored || false}
              @toggle-change=${(e) => this.handleInputChange({ 
                target: { 
                  name: 'uncensored', 
                  type: 'checkbox',
                  checked: e.detail.checked 
                } 
              })}>
            </toggle-switch>
          </label>
        </div>

        <div class="form-group reasoning-level-group">
          <label>Reasoning Effort:</label>
          <select name="thinking_level" 
                 value=${this.agent.thinking_level || 'off'}
                 @change=${this.handleInputChange}>
            <option value="off" 
                   ?selected=${(this.agent.thinking_level || 'off') === 'off'}>
              Off
            </option> 
            <option value="low" 
                   ?selected=${(this.agent.thinking_level || 'off') === 'low'}>
              Low
            </option>
            <option value="medium" 
                   ?selected=${(this.agent.thinking_level || 'off') === 'medium'}>
              Medium
            </option>
            <option value="high" 
                   ?selected=${(this.agent.thinking_level || 'off') === 'high'}>
              High
            </option>
          </select>
        </div>
        
        <div class="form-group commands-section">
          <details>
            <summary>Preferred Providers</summary>
            ${this.renderPreferredProviders()}
          </details>
        </div> 

        <div class="form-group commands-section" style="display: none;">
          <details>
            <summary>Required Plugins</summary>
            ${this.renderRequiredPlugins()}
          </details>
        </div>

        <div class="form-group commands-section">
          <label>Available Commands:</label>
          ${this.renderCommands()}
        </div>

        <div class="agent-insert-end"></div>
        <button class="btn" type="submit" ?disabled=${this.loading}>
          ${this.loading ? 'Saving...' : 'Save'}
        </button>
        
      </form>
    `;
  }
}

customElements.define('agent-form', AgentForm);
