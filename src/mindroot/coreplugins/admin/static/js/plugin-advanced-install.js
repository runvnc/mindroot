import { html, css } from './lit-core.min.js';
import { PluginBase } from './plugin-base.js';
import './plugin-install-dialog.js';

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

  firstUpdated() {
    super.firstUpdated();
    // Create the install dialog if it doesn't exist
    if (!this.installDialog) {
      this.installDialog = document.createElement('plugin-install-dialog');
      document.body.appendChild(this.installDialog);
    }
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Remove the dialog when component is removed
    if (this.installDialog && document.body.contains(this.installDialog)) {
      document.body.removeChild(this.installDialog);
    }
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

    // Extract repo name from URL - handle various GitHub URL formats
    let repoPath = githubUrl;
    
    // Handle full GitHub URLs
    if (githubUrl.includes('github.com/')) {
      const match = githubUrl.match(/github\.com\/([^/]+\/[^/]+)/);
      if (match) {
        repoPath = match[1];
      }
    }
    
    // Extract just the repo name for display
    const repoName = repoPath.split('/').pop();

    try {
      // Close the modal
      this.closeGitHubModal();

      // Open the installation dialog
      this.installDialog.open(repoName || 'GitHub Plugin', 'GitHub');
      
      // Connect to SSE endpoint for streaming GitHub installation
      // Build URL with properly encoded parameters
      const params = new URLSearchParams();
      params.append('plugin', repoName || 'plugin');
      params.append('source', 'github');
      params.append('source_path', repoPath);
      
      const eventSource = new EventSource(`/plugin-manager/stream-install-plugin?${params.toString()}`);
      
      eventSource.addEventListener('message', (event) => {
        this.installDialog.addOutput(event.data, 'info');
      });
      
      eventSource.addEventListener('error', (event) => {
        this.installDialog.addOutput(event.data, 'error');
      });
      
      eventSource.addEventListener('warning', (event) => {
        this.installDialog.addOutput(event.data, 'warning');
      });
      
      eventSource.addEventListener('complete', (event) => {
        this.installDialog.addOutput(event.data, 'success');
        this.installDialog.setComplete(false);
        eventSource.close();
        // Dispatch event for parent components to refresh their lists
        this.dispatch('plugin-installed', { plugin: { name: repoName, source: 'github' } });
      });
      
      eventSource.onerror = () => {
        eventSource.close();
        this.installDialog.setComplete(true);
      };
    } catch (error) {
      this.installDialog.addOutput(`Failed to install plugin from GitHub: ${error.message}`, 'error');
      this.installDialog.setComplete(true);
    }
  }

  async handleScanDirectory() {
    const directory = prompt('Enter the directory path to scan for plugins:');
    if (!directory) return;
    
    // Open the installation dialog
    this.installDialog.open('Directory Scan', 'Local Directory');
    this.installDialog.addOutput(`Scanning directory: ${directory}`, 'info');

    try {
      // Make the API call
      const response = await this.apiCall('/plugin-manager/scan-directory', 'POST', { directory });
      
      if (response.success) {
        this.installDialog.addOutput(response.message, 'success');
        
        // Show index compatibility info
        if (response.addable_to_index !== undefined) {
          this.installDialog.addOutput(`Index-compatible plugins: ${response.addable_to_index}/${response.plugins.length}`, 'info');
        }
        if (response.warning) {
          this.installDialog.addOutput(response.warning, 'warning');
        }
        
        // If plugins were found, list them
        if (response.plugins && response.plugins.length > 0) {
          this.installDialog.addOutput('Found plugins:', 'info');
          response.plugins.forEach(plugin => {
            this.installDialog.addOutput(`- ${plugin.name}: ${plugin.description || 'No description'}`, 'info');
          });
        } else {
          this.installDialog.addOutput('No plugins found in directory.', 'warning');
        }
        
        this.installDialog.setComplete(false);
        this.dispatch('plugins-scanned');
      } else {
        this.installDialog.addOutput(`Scan failed: ${response.message}`, 'error');
        this.installDialog.setComplete(true);
      }
    } catch (error) {
      this.installDialog.addOutput(`Failed to scan directory: ${error.message}`, 'error');
      
      // If there's a detailed error message, show it
      if (error.response && error.response.data && error.response.data.message) {
        this.installDialog.addOutput(error.response.data.message, 'error');
      }
      
      this.installDialog.setComplete(true);
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
