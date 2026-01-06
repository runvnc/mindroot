// Registry Settings functionality
export class RegistrySettings {
  constructor(component) {
    this.component = component;
    this.loadRegistryUrl();
  }

  loadRegistryUrl() {
    // Load from localStorage, environment variable, or default
    this.component.registryUrl = localStorage.getItem('registry_url') || 
                                window.MR_REGISTRY_URL || 
                                'https://registry.mindroot.io';
  }

  updateRegistryUrl(newUrl) {
    this.component.registryUrl = newUrl;
    localStorage.setItem('registry_url', newUrl);
    // Clear auth token when URL changes
    this.component.logout();
    // Reload stats with new URL
    this.component.loadStats();
  }

  renderSettings() {
    return `
      <details class="settings-section">
        <summary>
          <span class="material-icons">settings</span>
          <span>Settings</span>
        </summary>
        <div class="section">
          <h4>Registry Configuration</h4>
          <div class="form-row">
            <label for="registry-url">Registry URL:</label>
            <input type="url" 
                   id="registry-url" 
                   value="${this.component.registryUrl}"
                   placeholder="https://registry.mindroot.io">
            <button onclick="registrySettings.handleUrlChange()">Update URL</button>
            <button onclick="registrySettings.testConnection()">Test Connection</button>
          </div>
          <p class="help-text">
            Default: https://registry.mindroot.io or MR_REGISTRY_URL environment variable
          </p>
        </div>
      </details>
    `;
  }

  handleUrlChange() {
    const input = document.getElementById('registry-url');
    if (input && input.value) {
      this.updateRegistryUrl(input.value);
    }
  }

  async testConnection() {
    try {
      const response = await fetch(`${this.component.registryUrl}/alive`);
      if (response.ok) {
        alert('Connection successful!');
      } else {
        alert('Connection failed: Server responded with status ' + response.status);
      }
    } catch (error) {
      alert('Connection failed: ' + error.message);
    }
  }
}
