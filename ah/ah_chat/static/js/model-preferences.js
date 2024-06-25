import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class ModelPreferences extends BaseEl {
  static properties = {
    settings: { type: Array },
    organizedData: { type: Array }
  };

  constructor() {
    super();
    this.settings = [];
    this.organizedData = [];
    this.fetchSettings();
    this.fetchOrganizedData();
    setTimeout(() => {
      console.log("Done fetching data");
      console.log({ settings: this.settings, organizedData: this.organizedData });
      this.requestUpdate();
    }, 500);
  }

  async fetchSettings() {
    const response = await fetch('/settings');
    this.settings = await response.json();
  }

  async fetchOrganizedData() {
    const response = await fetch('/organized_models');
    this.organizedData = await response.json();
    console.log(this.organizedData)
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    this.setting = { ...this.setting, [name]: inputValue };
  }

  async handleSubmit(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const settings = [];

    formData.forEach((value, key) => {
      const [service, flag] = key.split("_._")
      const setting = { "service_or_command_name": service, "flag": flag, "model": value }
      settings.push(setting)
    });
    console.log({settings})
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

  _render() {
    return html`
      <div>
        <h2>Preferred Models</h2>
        <form @submit=${this.handleSubmit}>
          ${this.organizedData.map(serviceData => html`
            <div>
              <h3>${serviceData.service}</h3>
              ${serviceData.flags.map(flagData => html`
                <div>
                  <label>
                    ${flagData.flag}:
                    <select name="${serviceData.service}_._${flagData.flag}" @change=${this.handleInputChange}>
                      ${flagData.models.map(model => html`
                        <option value="${model.model.name}">${model.provider.plugin} - ${model.model.name}</option>
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
