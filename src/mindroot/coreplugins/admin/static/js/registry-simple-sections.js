/**
 * Registry Simple Sections
 * 
 * Handles the Stats and Settings sections for the registry manager.
 * These are simpler sections with less complex logic.
 */

import { html } from '/admin/static/js/lit-core.min.js';

class RegistrySimpleSections {
  constructor(sharedState, mainComponent) {
    this.state = sharedState;
    this.main = mainComponent;
    this.services = null; // Will be set by main component
  }

  setServices(services) {
    this.services = services;
  }

  // === Event Handlers ===

  async updateRegistryUrl() {
    const newUrl = this.main.shadowRoot.querySelector('input[type="url"]').value;
    await this.services.updateRegistryUrl(newUrl);
  }

  async testConnection() {
    await this.services.testConnection();
  }

  // === Render Methods ===

  renderStats() {
    return html`
      <div class="section">
        <h3>Registry Statistics</h3>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">${this.main.stats.total_plugins || 0}</div>
            <div class="stat-label">Plugins</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.main.stats.total_agents || 0}</div>
            <div class="stat-label">Agents</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.main.stats.total_users || 0}</div>
            <div class="stat-label">Users</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">${this.main.stats.total_installs || 0}</div>
            <div class="stat-label">Installs</div>
          </div>
        </div>
      </div>
    `;
  }

  renderSettings() {
    return html`
      <div class="section">
        <h3>Registry Settings</h3>
        <div class="registry-url-display">
          Current registry: ${this.state.registryUrl}
        </div>
        <div class="form-row">
          <label>Registry URL:</label>
          <input type="url" 
                 placeholder="https://registry.mindroot.io" 
                 .value=${this.state.registryUrl}
                 @input=${(e) => this.state.registryUrl = e.target.value}>
          <button @click=${() => this.updateRegistryUrl()}>Update</button>
          <button @click=${() => this.testConnection()}>Test Connection</button>
        </div>
        ${this.main.error ? html`<div class="error">${this.main.error}</div>` : ''}
        <div class="help-text">
          Configure the MindRoot Registry URL. Default is https://registry.mindroot.io
        </div>
      </div>
    `;
  }
}

export { RegistrySimpleSections };