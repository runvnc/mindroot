import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class PluginToggle extends BaseEl {
  static properties = {
    plugins: { type: Array }
  }

  static styles = [
    css`
      .plugin-toggle { /* styles */ }
      .plugin-item { /* styles */ }
      .buttons { /* styles */ }
    `
  ];

  constructor() {
    super();
    this.plugins = [];
    this.fetchPlugins();
  }

  async fetchPlugins() {
    const response = await fetch('/get-plugins');
    const data = await response.json();
    console.log({plugins: this.plugins})
    this.plugins  = []
    const {plugins} = data
    for (let [category, val] of Object.entries(plugins)) {
      for (let [name, data ] of Object.entries(val)) {
        data.name = name
        this.plugins.push(data)
      }
    }
    console.log({newPlugins: this.plugins})
  }

  handleToggle(event, plugin) {
    plugin.enabled = event.detail.checked;
    this.requestUpdate();
  }

  async handleSubmit() {
    const response = await fetch('/update-plugins', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugins: this.plugins.reduce((acc, plugin) => {
        acc[plugin.name] = plugin.enabled;
        return acc;
      }, {}) })
    });
    if (response.ok) {
      alert('Plugins updated successfully');
    } else {
      alert('Failed to update plugins');
    }
  }

  handleCancel() {
    this.fetchPlugins();
  }

  _render() {
    return html`
        ${this.plugins.map(plugin => html`
          <div class="plugin-item">
            <label>
              <toggle-switch .checked=${plugin.enabled} @toggle-change=${(e) => this.handleToggle(e, plugin)}></toggle-switch>
              ${plugin.name}
            </label>
          </div>
        `)}
        <div class="buttons">
          <button @click=${this.handleSubmit}>Submit</button>
          <button @click=${this.handleCancel}>Cancel</button>
        </div>
    `;
  }
}

customElements.define('plugin-toggle', PluginToggle);
