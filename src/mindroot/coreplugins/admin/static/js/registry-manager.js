import { html } from '/admin/static/js/lit-core.min.js';
import { RegistryManagerBase } from './registry-manager-base.js';
import { RegistrySharedServices } from './registry-shared-services.js';
import { RegistryAuthSection } from './registry-auth-section.js';
import { RegistrySearchSection } from './registry-search-section.js';
import { RegistryPublishSection } from './registry-publish-section.js';
import { RegistrySimpleSections } from './registry-simple-sections.js';
import "./mcp-publisher.js";

class RegistryManager extends RegistryManagerBase {
  constructor() {
    super();
    this.localMcpServers = [];
    this.searchTimeout = null;
    
    // Initialize shared state
    this.sharedState = {
      authToken: this.authToken,
      currentUser: this.currentUser,
      isLoggedIn: this.isLoggedIn,
      localContent: {},
      loading: this.loading,
      registryUrl: this.registryUrl,
      localPlugins: this.localPlugins,
      localAgents: this.localAgents
    };
    
    this.initializeModules();
  }
  
  initializeModules() {
    // Initialize services first
    this.services = new RegistrySharedServices(this.sharedState, this);
    
    // Initialize sections
    this.authSection = new RegistryAuthSection(this.sharedState, this);
    this.searchSection = new RegistrySearchSection(this.sharedState, this);
    this.publishSection = new RegistryPublishSection(this.sharedState, this);
    this.simpleSections = new RegistrySimpleSections(this.sharedState, this);
    
    // Set services reference for all sections
    this.authSection.setServices(this.services);
    this.searchSection.setServices(this.services);
    this.publishSection.setServices(this.services);
    this.simpleSections.setServices(this.services);
    
    // Initialize data
    this.services.checkAuthStatus();
    this.services.loadStats();
    this.services.loadLocalContent();
  }

  // Return true if an agent with this name is already present in localAgents
  isAgentInstalled(name) {
    return (this.localAgents || []).some(a => a.name === name);
  }

  // === MCP Server Management (kept in main component for now) ===

  async toggleMcpServerConnection(serverName, connect) {
    this.loading = true;
    const action = connect ? 'connect' : 'disconnect';
    try {
      const response = await fetch(`/admin/mcp/${action}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        this.showToast(`Server '${serverName}' ${action}ed successfully.`, 'success');
        await this.services.loadLocalContent();
      } else {
        const err = await response.json();
        throw new Error(err.detail || `Failed to ${action} server`);
      }
    } catch (error) {
      this.showToast(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  async removeMcpServer(serverName) {
    if (!confirm(`Are you sure you want to remove the MCP server '${serverName}'?`)) return;
    this.loading = true;
    try {
      const response = await fetch('/admin/mcp/remove', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_name: serverName })
      });
      if (response.ok) {
        this.showToast(`Server '${serverName}' removed.`, 'success');
        await this.services.loadLocalContent();
      } else {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to remove server');
      }
    } catch (error) {
      this.showToast(`Error: ${error.message}`, 'error');
    } finally {
      this.loading = false;
    }
  }

  // === Main Render Method ===

  _render() {
    return html`
      <div class="registry-manager">
        ${this.renderToasts()}
        ${this.authSection.renderHeader()}
        ${this.renderTabs()}
        ${this.renderContent()}
      </div>
    `;
  }

  renderTabs() {
    return html`
      <div class="tabs">
        <div class="tab ${this.activeTab === 'search' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'search'}>Search</div>
        <div class="tab ${this.activeTab === 'publish' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'publish'}>Publish</div>
        <div class="tab ${this.activeTab === 'stats' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'stats'}>Stats</div>
        <div class="tab ${this.activeTab === 'settings' ? 'active' : ''}" 
             @click=${() => this.activeTab = 'settings'}>Settings</div>
      </div>
    `;
  }

  renderContent() {
    switch (this.activeTab) {
      case 'search':
        return this.searchSection.renderSearch();
      case 'publish':
        return this.publishSection.renderPublish();
      case 'stats':
        return this.simpleSections.renderStats();
      case 'settings':
        return this.simpleSections.renderSettings();
      default:
        return this.searchSection.renderSearch();
    }
  }

  // === Legacy Methods (for backward compatibility) ===
  // These delegate to the services

  async checkAuthStatus() {
    return this.services.checkAuthStatus();
  }

  async loadStats() {
    return this.services.loadStats();
  }

  async loadLocalContent() {
    return this.services.loadLocalContent();
  }

  async handleLogin() {
    return this.authSection.handleLogin();
  }

  async login(username, password) {
    return this.services.login(username, password);
  }

  async handleRegister() {
    return this.authSection.handleRegister();
  }

  async register(username, email, password) {
    return this.services.register(username, email, password);
  }

  toggleRegisterForm() {
    return this.authSection.toggleRegisterForm();
  }

  logout() {
    return this.authSection.logout();
  }

  async loadTopContent() {
    return this.services.loadTopContent();
  }

  async search(query, category) {
    return this.services.search(query, category);
  }

  handleSearchInput(e) {
    return this.searchSection.handleSearchInput(e);
  }

  handleCategoryChange(category) {
    return this.searchSection.handleCategoryChange(category);
  }

  async installFromRegistry(item) {
    return this.services.installFromRegistry(item);
  }

  async installMcpServer(item) {
    return this.services.installMcpServer(item);
  }

  async installOAuthMcpServer(item) {
    return this.services.installOAuthMcpServer(item);
  }

  async installPlugin(item) {
    return this.services.installPlugin(item);
  }

  async installAgent(item) {
    return this.services.installAgent(item);
  }

  async handlePublishPluginFromGithub() {
    return this.publishSection.handlePublishPluginFromGithub();
  }

  async refreshOwnershipCache() {
    return this.services.refreshOwnershipCache();
  }

  async publishItem(item, type) {
    return this.publishSection.publishItem(item, type);
  }

  async updateRegistryUrl(newUrl) {
    return this.services.updateRegistryUrl(newUrl);
  }

  async testConnection() {
    return this.services.testConnection();
  }

  // === Utility Methods ===

  showSuccessMessage(message) {
    this.error = '';
    this.requestUpdate();
    
    setTimeout(() => {
      this.publishSuccess = '';
      this.requestUpdate();
    }, 5000);
  }

  showErrorMessage(message) {
    this.error = message;
    this.publishSuccess = '';
    this.requestUpdate();
  }
}

customElements.define('registry-manager', RegistryManager);