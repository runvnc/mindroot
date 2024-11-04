import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class PluginManager extends BaseEl {
  static properties = {
    plugins: { type: Array },
  }

  static styles = [
    css`
      .github-modal {
        padding: 20px;
        border: none;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);    
      }

      .form-group {
        margin-bottom: 15px;
      }

      .form-group label {
        display: block;
        margin-bottom: 5px;
      }

      .form-group input {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
      }

      .button-group {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
      }

      .button-group button {
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
      }
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

  showGitHubInstallModal() {
    const modal = this.shadowRoot.querySelector('#github-install-modal');
    modal.showModal({ modal: true, focus: true, center: true })
  }

  async handleGitHubInstall(e) {
    e.preventDefault();
    const modal = this.shadowRoot.querySelector('#github-install-modal');
    const githubUrl = this.shadowRoot.querySelector('#github-url').value;

    if (!githubUrl) {
      alert('Please fill in all fields');
      return;
    }

    const response = await fetch('/plugin-manager/install-x-github-plugin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ plugin:'test', url: githubUrl })
    });

    const result = await response.json();
    if (result.success) {
      alert(`Plugin installed successfully from GitHub`);
      this.fetchPlugins();
      modal.close();
    } else {
      alert(`Failed to install plugin from GitHub: ${result.message}`);
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
          <button @click=${this.showGitHubInstallModal}>Install from GitHub</button>
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
      <dialog id="github-install-modal" class="github-modal">
        <form method="dialog">
          <h2>Install Plugin from GitHub</h2>
          <div class="form-group">
            <label for="github-url">GitHub Repo</label>
            <input type="text" id="github-url" placeholder="e.g. user/repo or user/repo:tag" required>
          </div>
          <div class="button-group">
            <button value="cancel">Cancel</button>
            <button value="install" @click=${this.handleGitHubInstall}>Install</button>
          </div>
        </form>
      </dialog>
    `;
  }
}

customElements.define('plugin-manager', PluginManager);
