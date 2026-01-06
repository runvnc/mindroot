import { BaseEl } from './base.js';
import { html, css } from './lit-core.min.js';

class MissingCommands extends BaseEl {
  static properties = {
    agentName: { type: String },
    missingCommands: { type: Object },
    commandPluginMapping: { type: Object },
    installQueue: { type: Array },
    recommendedPlugins: { type: Array },
    loading: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }
    
    .missing-commands {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    
    .command-item {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      overflow: visible;
      border-radius: 8px;
      padding: 1rem;
    }
    
    .command-name {
      font-weight: bold;
      margin-bottom: 0.5rem;
      overflow-wrap: break-word;
      word-break: break-all;
    }
    
    .plugin-options {
      margin-top: 0.5rem;
    }
    
    .plugin-option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .plugin-option:last-child {
      border-bottom: none;
    }
    
    .queue-btn {
      background: #2a2a40;
      color: #fff;
      border: none;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .queue-btn:hover {
      background: #3a3a50;
    }
    
    .queue-btn.queued {
      background: #4a4a60;
      cursor: not-allowed;
    }
    
    .install-queue {
      margin-top: 1rem;
      padding: 1rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
    }
    
    .install-btn {
      background: #2a2a40;
      color: #fff;
      border: none;
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      margin-top: 0.5rem;
    }
    
    .install-btn:hover {
      background: #3a3a50;
    }
  `;

  constructor() {
    super();
    this.missingCommands = {};
    this.commandPluginMapping = {};
    this.recommendedPlugins = [];
    this.installQueue = [];
    this.loading = false;
  }

  updated(changedProperties) {
    if (changedProperties.has('agentName') && this.agentName) {
      this.fetchData();
    }
  }

  async fetchData() {
    this.loading = true;
    try {
      // Fetch missing commands
      const commandsResponse = await fetch(`/admin/missing-commands/${this.agentName}`);
      this.missingCommands = await commandsResponse.json();
      
      // Fetch command-plugin mapping
      const mappingResponse = await fetch('/admin/commands/command-plugin-mapping');
      this.commandPluginMapping = await mappingResponse.json();
      
      // Fetch agent data to get recommended plugins
      const agentResponse = await fetch(`/agents/local/${this.agentName}`);
      if (agentResponse.ok) {
        const agentData = await agentResponse.json();
        this.recommendedPlugins = agentData.recommended_plugins || agentData.required_plugins || [];
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      this.loading = false;
    }
  }

  queuePlugin(plugin) {
    if (!this.installQueue.some(p => p.name === plugin.name)) {
      this.installQueue = [...this.installQueue, plugin];
    }
  }

  async installQueuedPlugins() {
    if (this.installQueue.length === 0) return;
    
    this.loading = true;
    try {
      const response = await fetch('/admin/commands/install-queued-plugins', {
        method: 'POST'
      });
      const result = await response.json();
      
      // Clear queue on success
      if (result.status === 'completed') {
        this.installQueue = [];
        // Refresh data
        await this.fetchData();
      }
    } catch (error) {
      console.error('Error installing plugins:', error);
    } finally {
      this.loading = false;
    }
  }

  async installRecommendedPlugins() {
    if (this.recommendedPlugins.length === 0) return;
    
    this.loading = true;
    try {
      const response = await fetch(`/admin/install-recommended-plugins/${this.agentName}`, {
        method: 'POST'
      });
      const result = await response.json();
      this.displayInstallationResults(result);
      
      // Refresh data after installation
      await this.fetchData();
      
      return result;
    } catch (error) {
      console.error('Error installing recommended plugins:', error);
    } finally {
      this.loading = false;
    }
  }

  displayInstallationResults(result) {
    if (!result || !result.results) return;
    
    // Create a summary of installation results
    const successful = result.results.filter(r => r.status === 'success').length;
    const alreadyInstalled = result.results.filter(r => r.status === 'already_installed').length;
    const failed = result.results.filter(r => r.status === 'error').length;
    
    let message = `Installation summary: `;
    if (successful > 0) message += `${successful} installed successfully. `;
    if (alreadyInstalled > 0) message += `${alreadyInstalled} already installed. `;
    if (failed > 0) message += `${failed} failed to install.`;
    
    // Show detailed results for each plugin
    let details = result.results.map(r => {
      if (r.status === 'success') return `✅ ${r.plugin}: Successfully installed`;
      if (r.status === 'already_installed') return `ℹ️ ${r.plugin}: Already installed`;
      if (r.status === 'error') return `❌ ${r.plugin}: Failed - ${r.message}`;
      return `${r.plugin}: Unknown status ${r.status}`;
    }).join('\n');
    
    // Display the results using an alert for now
    // In a real application, you might want to use a modal or toast notification
    alert(`${message}\n\nDetails:\n${details}`);
  }

  renderMissingCommands() {
    if (Object.keys(this.missingCommands).length === 0) {
      return html`<div>No missing commands found for this agent.</div>`;
    }
    
    return Object.entries(this.missingCommands).map(([command, plugins]) => html`
      <div class="command-item">
        <div class="command-name">${command}</div>
        <div class="plugin-options">
          ${plugins && plugins.length > 0 ? 
            plugins.map(plugin => html`
              <div class="plugin-option">
                <span>${plugin.name} (${plugin.category})</span>
                <button 
                  class="queue-btn ${this.installQueue.some(p => p.name === plugin.name) ? 'queued' : ''}"
                  ?disabled=${this.installQueue.some(p => p.name === plugin.name) || plugin.enabled}
                  @click=${() => this.queuePlugin(plugin)}
                >
                  ${plugin.enabled ? 'Enabled' : this.installQueue.some(p => p.name === plugin.name) ? 'Queued' : 'Queue'}
                </button>
              </div>
            `) : 
            html`<div>No plugins found that provide this command</div>`
          }
        </div>
      </div>
    `);
  }

  renderInstallQueue() {
    if (this.installQueue.length === 0) return html``;
    
    return html`
      <div class="install-queue">
        <h3>Installation Queue</h3>
        <ul>
          ${this.installQueue.map(plugin => html`
            <li>${plugin.name}</li>
          `)}
        </ul>
        <button 
          class="install-btn" 
          @click=${this.installQueuedPlugins}
          ?disabled=${this.loading}
        >
          ${this.loading ? 'Installing...' : 'Install Plugins'}
        </button>
      </div>
    `;
  }

  _render() {
    return html`
      <div class="missing-commands">
        <h2>Missing Commands for ${this.agentName}</h2>
        ${this.loading ? 
          html`<div>Loading...</div>` : 
          html`
            ${this.renderMissingCommands()}
            ${this.renderInstallQueue()}
          `
        }
      </div>
    `;
  }
}

customElements.define('missing-commands', MissingCommands);
