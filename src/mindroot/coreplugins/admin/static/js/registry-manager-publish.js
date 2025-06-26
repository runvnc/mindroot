// Additional methods for publishing functionality

export function addPublishMethods(RegistryManager) {
  // Add publish tab to tabs
  RegistryManager.prototype.renderTabsWithPublish = function() {
    return `
      <div class="tabs">
        <div class="tab ${this.activeTab === 'search' ? 'active' : ''}" 
             onclick="this.activeTab = 'search'; this.requestUpdate();">Search</div>
        ${this.isLoggedIn ? `
          <div class="tab ${this.activeTab === 'publish' ? 'active' : ''}" 
               onclick="this.activeTab = 'publish'; this.requestUpdate();">Publish</div>
        ` : ''}
        <div class="tab ${this.activeTab === 'stats' ? 'active' : ''}" 
             onclick="this.activeTab = 'stats'; this.requestUpdate();">Stats</div>
      </div>
    `;
  };

  // Render publish content
  RegistryManager.prototype.renderPublish = function() {
    if (!this.isLoggedIn) {
      return `
        <div class="section">
          <h3>Publish to Registry</h3>
          <p>Please log in to publish content.</p>
        </div>
      `;
    }

    return `
      <div class="section">
        <h3>Publish Plugin</h3>
        <div class="publish-form">
          <input type="text" placeholder="Plugin Title" id="plugin-title">
          <textarea placeholder="Description" id="plugin-description"></textarea>
          <input type="text" placeholder="Version (e.g., 1.0.0)" id="plugin-version">
          <input type="text" placeholder="GitHub URL (e.g., user/repo)" id="plugin-github">
          <input type="text" placeholder="OR PyPI Module Name" id="plugin-pypi">
          <input type="text" placeholder="Tags (comma separated)" id="plugin-tags">
          <button class="primary" onclick="this.handlePublishPlugin()">Publish Plugin</button>
        </div>
      </div>
      
      <div class="section">
        <h3>Publish Agent</h3>
        <div class="publish-form">
          <select id="agent-select">
            <option value="">Select an agent...</option>
            ${this.localAgents.map(agent => `<option value="${agent.name}">${agent.name}</option>`).join('')}
          </select>
          <textarea placeholder="Description" id="agent-description"></textarea>
          <input type="text" placeholder="Version (e.g., 1.0.0)" id="agent-version">
          <input type="text" placeholder="Tags (comma separated)" id="agent-tags">
          <button class="primary" onclick="this.handlePublishAgent()">Publish Agent</button>
        </div>
      </div>
    `;
  };

  // Handle plugin publishing
  RegistryManager.prototype.handlePublishPlugin = async function() {
    const title = this.shadowRoot.getElementById('plugin-title').value;
    const description = this.shadowRoot.getElementById('plugin-description').value;
    const version = this.shadowRoot.getElementById('plugin-version').value;
    const githubUrl = this.shadowRoot.getElementById('plugin-github').value;
    const pypiModule = this.shadowRoot.getElementById('plugin-pypi').value;
    const tags = this.shadowRoot.getElementById('plugin-tags').value;
    
    if (!title || !description || !version) {
      this.error = 'Please fill in title, description, and version';
      this.requestUpdate();
      return;
    }
    
    if (!githubUrl && !pypiModule) {
      this.error = 'Please provide either GitHub URL or PyPI module name';
      this.requestUpdate();
      return;
    }
    
    const publishData = {
      title: title,
      description: description,
      category: 'plugin',
      content_type: 'mindroot_plugin',
      version: version,
      data: {
        source: githubUrl ? 'github' : 'pypi',
        installation_notes: 'Install via MindRoot admin interface'
      },
      github_url: githubUrl || null,
      pypi_module: pypiModule || null,
      tags: tags ? tags.split(',').map(t => t.trim()) : []
    };
    
    await this.publishToRegistry(publishData);
  };

  // Handle agent publishing
  RegistryManager.prototype.handlePublishAgent = async function() {
    const selectedAgent = this.shadowRoot.getElementById('agent-select').value;
    const description = this.shadowRoot.getElementById('agent-description').value;
    const version = this.shadowRoot.getElementById('agent-version').value;
    const tags = this.shadowRoot.getElementById('agent-tags').value;
    
    if (!selectedAgent || !description || !version) {
      this.error = 'Please select an agent and fill in description and version';
      this.requestUpdate();
      return;
    }
    
    const agentData = this.localAgents.find(agent => agent.name === selectedAgent);
    if (!agentData) {
      this.error = 'Selected agent not found';
      this.requestUpdate();
      return;
    }
    
    const publishData = {
      title: selectedAgent,
      description: description,
      category: 'agent',
      content_type: 'mindroot_agent',
      version: version,
      data: agentData,
      tags: tags ? tags.split(',').map(t => t.trim()) : []
    };
    
    await this.publishToRegistry(publishData);
  };

  // Publish to registry
  RegistryManager.prototype.publishToRegistry = async function(publishData) {
    this.loading = true;
    this.error = '';
    
    try {
      const response = await fetch(`${this.registryUrl}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`
        },
        body: JSON.stringify(publishData)
      });
      
      if (response.ok) {
        this.error = 'Published successfully!';
        // Clear form fields
        setTimeout(() => {
          this.error = '';
          this.requestUpdate();
        }, 3000);
      } else {
        const errorData = await response.json();
        this.error = errorData.detail || 'Publishing failed';
      }
    } catch (error) {
      this.error = 'Network error: ' + error.message;
    }
    
    this.loading = false;
    this.requestUpdate();
  };
}
