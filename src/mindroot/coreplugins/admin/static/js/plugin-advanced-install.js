import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';

export class PluginAdvancedInstall extends PluginBase {
  static properties = {
    ...PluginBase.properties,
    showGitHubModal: { type: Boolean }
  }

  static styles = [
    PluginBase.styles,
    css`
      .advanced-install {
        margin-top: 20px;
        padding-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
      }

      .install-options {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
      }

      .github-modal {
        background: rgb(15, 15, 30);
        padding: 20px;
        border: none;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        color: #f0f0f0;
      }

      .github-modal::backdrop {
        background: rgba(0, 0, 0, 0.7);
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
        background: rgb(25, 25, 50);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        color: #f0f0f0;
      }

      .button-group {
        display: flex;
        justify-content: flex-end;
        gap: 10px;
        margin-top: 20px;
      }

      h3 {
        margin-bottom: 15px;
        color: #888;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
    `
  ];

  constructor() {
    super();
    this.showGitHubModal = false;
  }

  openGitHubModal() {
    const modal = this.shadowRoot.querySelector('#github-install-modal');
    modal.showModal();
  }

  closeGitHubModal() {
    const modal = this.shadowRoot.querySelector('#github-install-modal');
    modal.close();
  }

  async handleGitHubInstall(e) {
    e.preventDefault();
    const githubUrl = this.shadowRoot.querySelector('#github-url').value;

    if (!githubUrl) {
      alert('Please enter a GitHub repository URL');
      return;
    }

    try {
      await this.apiCall('/plugin-manager/install-x-github-plugin', 'POST', {
        plugin: 'test',
        url: githubUrl
      });
      
      alert('Plugin installed successfully from GitHub');
      this.closeGitHubModal();
      this.dispatch('plugin-installed');
    } catch (error) {
      alert(`Failed to install plugin from GitHub: ${error.message}`);
    }
  }

  async handleScanDirectory() {
    const directory = prompt('Enter the directory path to scan for plugins:');
    if (!directory) return;

    try {
      await this.apiCall('/plugin-manager/scan-directory', 'POST', { directory });
      alert('Directory scanned successfully');
      this.dispatch('plugins-scanned');
    } catch (error) {
      alert(`Failed to scan directory: ${error.message}`);
    }
  }

  _render() {
    return html`
      <div class="advanced-install">
        <h3>Advanced Installation</h3>
        
        <div class="install-options">
          <button @click=${this.handleScanDirectory}>
            <span class="material-icons">folder_open</span>
            Scan Local Directory
          </button>
          <button @click=${this.openGitHubModal}>
            <span class="material-icons">cloud_download</span>
            Install from GitHub
          </button>
        </div>

        <dialog id="github-install-modal" class="github-modal">
          <form method="dialog" @submit=${this.handleGitHubInstall}>
            <h2>Install Plugin from GitHub</h2>
            <div class="form-group">
              <label for="github-url">GitHub Repository URL</label>
              <input type="text" id="github-url"
                     placeholder="user/repo or user/repo:tag"
                     required>
            </div>
            <div class="button-group">
              <button type="button" @click=${this.closeGitHubModal}>Cancel</button>
              <button type="submit">Install</button>
            </div>
          </form>
        </dialog>
      </div>
    `;
  }
}

customElements.define('plugin-advanced-install', PluginAdvancedInstall);
