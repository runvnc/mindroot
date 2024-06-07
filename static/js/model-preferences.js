import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { BaseEl } from './base.js';

class ModelPreferences extends BaseEl {
  static properties = {
    settings: { type: Array },
    commands: { type: Array },
    services: { type: Array },
    flags: { type: Array },
    models: { type: Array },
    providers: { type: Array }
  };

  constructor() {
    super();
    this.settings = [];
    this.commands = [];
    this.services = [];
    this.flags = ['local', 'uncensored'];
    this.models = [];
    this.providers = [];
    this.fetchSettings();
    this.fetchCommands();
    this.fetchServices();
    this.fetchModels();
    this.fetchProviders();
  }

  async fetchSettings() {
    const response = await fetch('/settings');
    this.settings = await response.json();
  }

  async fetchCommands() {
    const response = await fetch('/commands');
    this.commands = await response.json();
  }

  async fetchServices() {
    const response = await fetch('/services');
    this.services = await response.json();
  }

  async fetchModels() {
    const response = await fetch('/models');
    this.models = await response.json();
  }

  async fetchProviders() {
    const response = await fetch('/providers');
    this.providers = await response.json();
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    this.setting = { ...this.setting, [name]: inputValue };
  }

  async handleSubmit(event) {
    event.preventDefault();
    const method = this.newSetting ? 'POST' : 'PUT';
    const url = this.newSetting ? '/settings' : `/settings/${this.setting.id}`;
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.setting)
    });
    if (response.ok) {
      alert('Setting saved successfully');
      this.fetchSettings();
    } else {
      alert('Failed to save setting');
    }
  }

  async handleDelete(settingId) {
    const response = await fetch(`/settings/${settingId}`, { method: 'DELETE' });
    if (response.ok) {
      alert('Setting deleted successfully');
      this.fetchSettings();
    } else {
      alert('Failed to delete setting');
    }
  }

  _render() {
    return html`
      <div>
        <h2>Preferred Models Settings</h2>
        <form @submit=${this.handleSubmit}>
          <div>
            <label>
              Service/Command Name:
              <select name="service_or_command_name" @change=${this.handleInputChange}>
                ${this.commands.map(command => html`
                  <option value="${command}">${command}</option>
                `)}
                ${this.services.map(service => html`
                  <option value="${service}">${service}</option>
                `)}
              </select>
            </label>
          </div>
          <div>
            <label>
              Positive Flags:
              ${this.flags.map(flag => html`
                <label>
                  <input type="checkbox" name="positive_flags" value="${flag}" @change=${this.handleInputChange} /> ${flag}
                </label>
              `)}
            </label>
          </div>
          <div>
            <label>
              Negative Flags:
              ${this.flags.map(flag => html`
                <label>
                  <input type="checkbox" name="negative_flags" value="${flag}" @change=${this.handleInputChange} /> ${flag}
                </label>
              `)}
            </label>
          </div>
          <div>
            <label>
              Provider:
              <select name="provider" @change=${this.handleInputChange}>
                ${this.providers.map(provider => html`
                  <option value="${provider.name}">${provider.name}</option>
                `)}
              </select>
            </label>
          </div>
          <div>
            <label>
              Model:
              <select name="model" @change=${this.handleInputChange}>
                ${this.models.map(model => html`
                  <option value="${model.name}">${model.name}</option>
                `)}
              </select>
            </label>
          </div>
          <button type="submit">Save</button>
        </form>
        <h3>Existing Settings</h3>
        <ul>
          ${this.settings.map(setting => html`
            <li>
              ${setting.service_or_command_name} - ${setting.provider} - ${setting.model}
              <button @click=${() => this.handleDelete(setting.id)}>Delete</button>
            </li>
          `)}
        </ul>
      </div>
    `;
  }
}

customElements.define('model-preferences', ModelPreferences);
