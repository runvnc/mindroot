/**
 * Registry Publish Section
 * 
 * Handles publishing workflows for plugins, agents, and MCP servers
 * to the registry.
 */

import { html } from '/admin/static/js/lit-core.min.js';

class RegistryPublishSection {
  constructor(sharedState, mainComponent) {
    this.state = sharedState;
    this.main = mainComponent;
    this.services = null; // Will be set by main component
  }

  setServices(services) {
    this.services = services;
  }

  // === Event Handlers ===

  async handlePublishPluginFromGithub() {
    const repoInput = this.main.shadowRoot.getElementById('plugin-github-repo');
    const repo = repoInput.value;
    
    const success = await this.services.publishPluginFromGithub(repo);
    if (success) {
      repoInput.value = '';
    }
    this.main.requestUpdate();
  }

  async refreshOwnershipCache() {
    await this.services.refreshOwnershipCache();
    this.main.requestUpdate();
  }

  async publishItem(item, type) {
    if (!this.state.isLoggedIn) {
      this.main.error = 'Please log in to publish items';
      this.main.requestUpdate();
      return;
    }

    this.state.loading = true;
    this.main.error = '';
    
    try {
      let publishData;
      
      if (type === 'agent') {
        publishData = await this.buildAgentPublishData(item);
      } else {
        throw new Error('Unknown item type');
      }
      
      const response = await fetch(`${this.state.registryUrl}/publish`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.state.authToken}`
        },
        body: JSON.stringify(publishData)
      });
      
      if (response.ok) {
        const result = await response.json();
        this.services.showToast(`Successfully published ${publishData.title}!`, 'success');
      } else {
        const errorData = await response.json();
        this.services.showToast(errorData.details || 'Publishing failed', 'error');
      }
    } catch (error) {
      this.services.showToast('Publishing failed: ' + error.message, 'error');
    }
    
    this.state.loading = false;
    this.main.requestUpdate();
  }

  // === Helper Methods ===

  async buildAgentPublishData(item) {
    // Load persona data if agent has a persona
    let personaData = null;
    let personaAssets = null;
    
    if (item.persona && typeof item.persona === 'string') {
      personaData = await this.loadPersonaData(item.persona);
      
      // Clean persona data - remove absolute file paths
      if (personaData) {
        delete personaData.avatar_image_path;
        delete personaData.face_ref_image_path;
        delete personaData.avatar;
        delete personaData.faceref;
      }
      
      // Load and upload persona assets to registry
      const localAssets = await this.uploadPersonaAssets(item.persona);
      if (Object.keys(localAssets).length > 0) {
        const assetData = await this.convertAssetsToBase64(localAssets);
        if (personaData) {
          personaData.persona_assets = assetData;
          console.log('Added asset data to persona data:', Object.keys(assetData));
        }
        personaAssets = assetData;
      }
    }
    
    return {
      title: item.name,
      description: item.description || `${item.name} agent`,
      category: 'agent',
      content_type: 'mindroot_agent',
      version: item.version || '1.0.0',
      data: {
        agent_config: item,
        persona_ref: personaData ? {
          name: personaData.name,
          owner: this.state.currentUser?.username,
          version: personaData.version || '1.0.0',
          original_path: item.persona
        } : null,
        persona_data: personaData,
        persona_assets: personaAssets,
        persona: item.persona || personaData?.name || {},
        instructions: item.instructions || '',
        model: item.model || 'default'
      },
      tags: item.tags || ['agent'],
      dependencies: item.dependencies || []
    };
  }

  async loadPersonaData(personaRef) {
    try {
      let personaPath;
      if (personaRef.startsWith('registry/')) {
        personaPath = `/personas/${personaRef}`;
      } else {
        personaPath = `/personas/local/${personaRef}`;
      }
      
      const response = await fetch(personaPath);
      if (response.ok) {
        return await response.json();
      }
      
      if (!personaRef.startsWith('registry/')) {
        const sharedResponse = await fetch(`/personas/shared/${personaRef}`);
        if (sharedResponse.ok) {
          return await sharedResponse.json();
        }
      }
      
      return null;
    } catch (error) {
      console.error('Error loading persona data:', error);
      return null;
    }
  }

  async uploadPersonaAssets(personaRef) {
    try {
      console.log('Uploading persona assets for:', personaRef);
      const assets = {};
      
      // Check for avatar image
      const avatarPath = `/chat/personas/${personaRef}/avatar.png`;
      try {
        const avatarResponse = await fetch(avatarPath);
        if (avatarResponse.ok) {
          const avatarBlob = await avatarResponse.blob();
          console.log('Found avatar image, size:', avatarBlob.size);
          assets.avatar = avatarBlob;
        }
      } catch (e) {
        console.log(`No avatar found for persona ${personaRef}`);
      }
      
      // Check for faceref image
      const facerefPath = `/chat/personas/${personaRef}/faceref.png`;
      try {
        const facerefResponse = await fetch(facerefPath);
        if (facerefResponse.ok) {
          const facerefBlob = await facerefResponse.blob();
          console.log('Found faceref image, size:', facerefBlob.size);
          assets.faceref = facerefBlob;
        }
      } catch (e) {
        console.log(`No faceref found for persona ${personaRef}`);
      }
      
      console.log('Total assets found:', Object.keys(assets).length);
      return assets;
    } catch (error) {
      console.error('Error loading persona assets for upload:', error);
      return {};
    }
  }

  async convertAssetsToBase64(assets) {
    try {
      console.log('Converting assets to base64:', Object.keys(assets));
      const assetData = {};
      
      for (const [assetType, blob] of Object.entries(assets)) {
        console.log(`Converting ${assetType} to base64...`);
        const arrayBuffer = await blob.arrayBuffer();
        const uint8Array = new Uint8Array(arrayBuffer);
        const binaryString = Array.from(uint8Array, byte => String.fromCharCode(byte)).join('');
        const base64String = btoa(binaryString);
        
        assetData[assetType] = {
          data: base64String,
          type: 'image/png',
          size: blob.size
        };
        console.log(`${assetType} converted successfully, size:`, blob.size);
      }
      
      console.log('Final asset data keys:', Object.keys(assetData));
      return assetData;
    } catch (error) {
      console.error('Error converting assets to base64:', error);
      return {};
    }
  }

  // === Render Methods ===

  renderPublish() {
    if (!this.state.isLoggedIn) {
      return this.renderLoginRequired();
    }

    return html`
     <div class="publish-details">
      ${this.renderGithubPublishing()}
      ${this.renderLocalPublishing()}
      ${this.renderMcpPublishing()}
    </div>
    `;
  }

  renderLoginRequired() {
    return html`
      <div class="section">
        <h3>Publish to Registry</h3>
        <p>Please log in to publish plugins and agents to the registry.</p>
      </div>
    `;
  }

  renderGithubPublishing() {
    return html`
      <details>
        <summary>Publish Plugin from GitHub</summary>
        <div class="publish-form" style="max-width: 500px; display: flex; flex-direction: column; gap: 1rem;">
          <p>Enter the GitHub repository (e.g., user/repo) to publish a plugin directly to the registry.</p>
          <input type="text" placeholder="GitHub Repository (e.g., user/repo)" id="plugin-github-repo">
          <button class="primary" @click=${() => this.handlePublishPluginFromGithub()}>Publish from GitHub</button>
        </div>
      </details>
    `;
  }

  renderLocalPublishing() {
    return html`
      <!-- <div class="section"> -->
      <details>
        <summary>Publish Agent</summary>
        ${this.renderOwnershipInfo()}
        <p>Select a local plugin or agent to publish to the registry:</p>
        
        ${this.renderPublishingStatus()}
        ${this.renderLocalAgents()}
      </details>
      <!-- </div> -->
    `;
  }

  renderOwnershipInfo() {
    return html`
      <div class="form-row">
        <button @click=${() => this.refreshOwnershipCache()} ?disabled=${this.state.loading}>
          Refresh Ownership Info
        </button>
        <span class="help-text">
          Last scanned: ${this.main.agentOwnership?.scanned_at ? 
            new Date(this.main.agentOwnership.scanned_at).toLocaleString() : "Never"}
        </span>
      </div>
    `;
  }

  renderPublishingStatus() {
    if (this.state.loading) {
      return html`<div class="loading">Publishing...</div>`;
    }
    
    if (this.main.publishSuccess) {
      return html`<div class="success">${this.main.publishSuccess}</div>`;
    }
    
    if (this.main.error) {
      const isSuccess = this.main.error.includes("Successfully");
      return html`<div class="${isSuccess ? "success" : "error"}">${this.main.error}</div>`;
    }
    
    return '';
  }

  renderLocalAgents() {
    return html`
        <h4>Local Agents (${this.state.localAgents.length})</h4>
      ${this.state.localAgents.length === 0 ? html`
        <p class="help-text">No local agents found. Create some agents first to publish them.</p>
      ` : html`
        ${this.state.localAgents.map(agent => this.renderAgentItem(agent))}
      `}
    `;
  }

  renderAgentItem(agent) {
    const agentKey = `local/${agent.name}`;
    const ownershipInfo = this.main.agentOwnership?.agents?.[agentKey];
    const hasExternalOwner = ownershipInfo?.has_external_owner || false;
    const canPublish = !hasExternalOwner;
    const ownerName = ownershipInfo?.creator || ownershipInfo?.owner || ownershipInfo?.registry_owner || ownershipInfo?.created_by;
    
    return html`
      <div class="result-item">
        <h5 class="result-title">${agent.name}</h5>
        <p class="result-description">${agent.description || "No description available"}</p>
        ${hasExternalOwner ? html`
          <p class="help-text" style="color: #dc3545;">Cannot publish: Agent created by ${ownerName || "another user"}</p>
        ` : ""}
        <div class="result-actions">
          <button class="primary" 
                  @click=${() => this.publishItem(agent, "agent")} 
                  ?disabled=${this.state.loading || !canPublish}>
            Publish Agent
          </button>
        </div>
      </div>
    `;
  }

  renderMcpPublishing() {
    return html`
      <!-- <div class="section"> -->
     <!-- <details>
        <summary>
        <h3>MCP Server Registry</h3>
        </summary>
        <mcp-registry-browser></mcp-registry-browser>
      <!-- </div> 
      </details> -->
      
      <!-- <div class="section"> -->
      <details>
        <summary>Publish New MCP Server</summary>
        <mcp-publisher
          .registryUrl=${this.state.registryUrl}
          .authToken=${this.state.authToken}
          .isLoggedIn=${this.state.isLoggedIn}
        ></mcp-publisher>
      <!-- </div> -->
    </details>
    `;
  }
}

export { RegistryPublishSection };
