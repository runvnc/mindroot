import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { BaseEl } from './base.js';

class ModelPreferences extends BaseEl {
  static properties = {
    settings: { type: Array },
    commands: { type: Array },
    services: { type: Array },
    flags: { type: Array },
    models: { type: Array },
    providers: { type: Array },
    equivalentFlags: { type: Array }
  };

  constructor() {
    super();
    this.settings = [];
    this.commands = [];
    this.services = [];
    this.flags = ['local', 'uncensored'];
    this.models = [];
    this.providers = [];
    this.equivalentFlags = [];
    this.fetchSettings();
    this.fetchCommands();
    this.fetchServices();
    this.fetchModels();
    this.fetchProviders();
    this.fetchEquivalentFlags();
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

  async fetchEquivalentFlags() {
    const response = await fetch('/equivalent_flags');
    this.equivalentFlags = await response.json();
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    this.setting = { ...this.setting, [name]: inputValue };
  }

  async handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const settings = {};

    formData.forEach((value, key) => {
        const [service, flag] = key.split('_');
        if (!settings[service]) {
            settings[service] = {};
        }
        settings[service][flag] = value;
    });

    const response = await fetch('/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
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

  groupModelsByServiceAndFlag(models, equivalentFlags) {
    const serviceDict = {};
    const flagMapping = {};

    // Create a mapping of equivalent flags
    equivalentFlags.forEach(eqFlags => {
        eqFlags.forEach(flag => {
            flagMapping[flag] = eqFlags[0];
        });
    });

    // Group models by service and flag
    models.forEach(model => {
        model.services.forEach(service => {
            if (!serviceDict[service]) {
                serviceDict[service] = {};
            }
            let matchedFlag = false;
            model.flags.forEach(flag => {
                const equivalentFlag = flagMapping[flag] || flag;
                if (!serviceDict[service][equivalentFlag]) {
                    serviceDict[service][equivalentFlag] = [];
                }
                serviceDict[service][equivalentFlag].push(model);
                matchedFlag = true;
            });
            if (!matchedFlag) {
                if (!serviceDict[service]['no_flags']) {
                    serviceDict[service]['no_flags'] = [];
                }
                serviceDict[service]['no_flags'].push(model);
            }
        });
    });

    return serviceDict;
  }

  _render() {
    const groupedModels = this.groupModelsByServiceAndFlag(this.models, this.equivalentFlags);

    return html`
      <div>
        <h2>Preferred Models Settings</h2>
        <form @submit=${this.handleSubmit}>
          ${Object.keys(groupedModels).map(service => html`
            <div>
              <h3>${service}</h3>
              ${Object.keys(groupedModels[service]).map(flag => html`
                <div>
                  <label>
                    ${flag}:
                    <select name="${service}_${flag}" @change=${this.handleInputChange}>
                      ${groupedModels[service][flag].map(model => html`
                        <option value="${model.name}">${model.name}</option>
                      `)}
                    </select>
                  </label>
                </div>
              `)}
            </div>
          `)}
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
