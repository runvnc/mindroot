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
    this.plugins = await response.json();
  }

  async handleScanDirectory() {
    let directory;
    if (window.showDirectoryPicker) {
      try {
        const dirHandle = await window.showDirectoryPicker();
        directory = dirHandle.name; // This is just the directory name, not the full path
      } catch (err) {
        console.log('User cancelled directory selection or it's not supported');
      }
    }
    
    if (!directory) {
      directory = prompt("Enter the directory path to scan for plugins:");
    }
    
    if (!directory) return;

    const response = await fetch('/plugin-manager/scan-directory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory })
    });

    if (response.ok) {
      alert('Directory scanned successfully');
      this.fetchPlugins();
    } else {
      alert('Failed to scan directory');
    }
  }

  async handleInstallLocal(plugin) {
    const response = await fetch('/plugin-manager/install-local-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name })
    });
    if (response.ok) {
      alert(`Plugin ${plugin.name} installed successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to install plugin ${plugin.name}`);
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
    if (response.ok) {
      alert(`Plugin ${plugin.name} installed successfully from GitHub`);
      this.fetchPlugins();
    } else {
      alert(`Failed to install plugin ${plugin.name} from GitHub`);
    }
  }

  async handleUpdate(plugin) {
    const response = await fetch('/plugin-manager/update-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name })
    });
    if (response.ok) {
      alert(`Plugin ${plugin.name} updated successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to update plugin ${plugin.name}`);
    }
  }

  async handleToggle(plugin) {
    const response = await fetch('/plugin-manager/toggle-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin: plugin.name, enabled: !plugin.enabled })
    });
    if (response.ok) {
      alert(`Plugin ${plugin.name} ${plugin.enabled ? 'disabled' : 'enabled'} successfully`);
      this.fetchPlugins();
    } else {
      alert(`Failed to toggle plugin ${plugin.name}`);
    }
  }

  _render() {
    return html`
      <div class="plugin-manager">
        <div class="scan-section">
          <button @click=${this.handleScanDirectory}>Scan Directory for Plugins</button>
        </div>

        <h3>Plugins</h3>
        ${this.plugins.map(plugin => html`
          <div class="plugin-item">
            <span>${plugin.name}</span>
            <span>${plugin.state}</span>
            <span>Source: ${plugin.source}</span>
            ${plugin.state === 'available' ? html`
              <button @click=${() => this.handleInstallLocal(plugin)}>Install</button>
            ` : ''}
            ${plugin.state === 'installable' ? html`
              <button @click=${() => this.handleInstallGitHub(plugin)}>Install from GitHub</button>
            ` : ''}
            ${plugin.state === 'installed' ? html`
              <button @click=${() => this.handleUpdate(plugin)}>Update</button>
              <button @click=${() => this.handleToggle(plugin)}>${plugin.enabled ? 'Disable' : 'Enable'}</button>
            ` : ''}
          </div>
        `)}
      </div>
    `;
  }
}

customElements.define('plugin-manager', PluginManager);
