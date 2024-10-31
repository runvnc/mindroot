import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class PluginManager extends BaseEl {
  static properties = {
    plugins: { type: Array },
  }

  static styles = [
    css`
      .plugin-manager { /* styles */ }
      .plugin-item { /* styles */ }
      .scan-section { /* styles */ }
      .buttons { /* styles */ }
    `
  ];

  constructor() {
    super();
    this.plugins = [];
    this.fetchPlugins();
  }

  async fetchPlugins() {
    const response = await fetch('/plugin-manager/get-all-plugins');
    const result = await response.json();
    if (result.success) {
      this.plugins = result.data;
      console.log({plugins: this.plugins});
    } else {
      console.error('Failed to fetch plugins:', result.message);
    }
  }

  async handleScanDirectory() {
    let directory = prompt("Enter the directory path to scan for plugins:");
    if (!directory) return;

    const response = await fetch('/plugin-manager/scan-directory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory })
    });

    const result = await response.json();
    if (result.success) {
      alert('Directory scanned successfully');
      this.fetchPlugins();
    } else {
      alert(`Failed to scan directory: ${result.message}`);
    }
  }

  async handleInstallLocal(plugin) {
    const response = await fetch('/plugin-manager/install-local-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name })
    });
    const result = await response.json();
    if (result.success) {
      alert(`Plugin ${plugin.name} installed successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to install plugin ${plugin.name}: ${result.message}`);
    }
  }

  async handleInstallGitHub(plugin) {
    const githubUrl = prompt(`Enter GitHub URL for ${plugin.name}:`);
    if (!githubUrl) return;

    const response = await fetch('/plugin-manager/install-github-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name, url: githubUrl })
    });
    const result = await response.json();
    if (result.success) {
      alert(`Plugin ${plugin.name} installed successfully from GitHub`);
      this.fetchPlugins();
    } else {
      alert(`Failed to install plugin ${plugin.name} from GitHub: ${result.message}`);
    }
  }

  async handleUpdate(plugin) {
    const response = await fetch('/plugin-manager/update-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name })
    });
    const result = await response.json();
    if (result.success) {
      alert(`Plugin ${plugin.name} updated successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to update plugin ${plugin.name}: ${result.message}`);
    }
  }

  async handleToggle(plugin) {
    const response = await fetch('/plugin-manager/toggle-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name, enabled: !plugin.enabled })
    });
    const result = await response.json();
    if (result.success) {
      alert(`Plugin ${plugin.name} ${plugin.enabled ? 'disabled' : 'enabled'} successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to toggle plugin ${plugin.name}: ${result.message}`);
    }
  }

  _render() {
    return html`
      <div class="plugin-manager">
        <div class="scan-section">
          <button @click=${this.handleScanDirectory}>Scan Directory for Plugins</button>
        </div>

        <h3>Plugins</h3>
        ${this.plugins.length ? this.plugins.map(plugin => html`
          <div class="plugin-item">
            <span>${plugin.name}</span>
            <span>${plugin.state}</span>
            <span>Source: ${plugin.source}</span>
            <span>Version: ${plugin.version}</span>
            ${plugin.state === 'available' ? html`
              <button @click=${() => this.handleInstallLocal(plugin)}>Install</button>
            ` : ''}
            ${plugin.state === 'installable' ? html`
              <button @click=${() => this.handleInstallGitHub(plugin)}>Install from GitHub</button>
            ` : ''}
            ${(plugin.state === 'installed' || plugin.category === 'core') ? html`
              <button @click=${() => this.handleInstallLocal(plugin)}>Update</button>
              <button @click=${() => this.handleToggle(plugin)}>${plugin.enabled ? 'Disable' : 'Enable'}</button>
            ` : ''}
          </div>
        `) : html`<p>No plugins found.</p>`}
      </div>
    `;
  }
}

customElements.define('plugin-manager', PluginManager);
