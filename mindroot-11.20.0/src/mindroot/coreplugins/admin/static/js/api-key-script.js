import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import showNotification from './notification.js';

class ApiKeyScript extends BaseEl {
  static properties = {
    agents: { type: Array },
    apiKeys: { type: Array },
    selectedAgent: { type: String },
    domainName: { type: String },
    apiKey: { type: String },
    scriptContent: { type: String },
    showPreview: { type: Boolean }
  };

  static styles = css`
    /* This component's styles are mostly for the form, not the global preview */
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }
    .api-key-script {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      gap: 20px;
    }
    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .form-group {
      margin-bottom: 15px;
    }
    .form-group label {
      display: block;
      margin-bottom: 5px;
      color: #f0f0f0;
      font-weight: 500;
    }
    input[type="text"],
    select {
      width: 100%;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }
    button {
      background: #2196F3;
      color: #fff;
      border: none;
      padding: 0.75rem 1.5rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-right: 10px;
    }
    button:hover {
      background: #1976D2;
    }
    button.secondary {
      background: #2a2a40;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .script-preview {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      padding: 1rem;
      font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
      font-size: 0.9rem;
      color: #f0f0f0;
      white-space: pre-wrap;
      max-height: 400px;
      overflow-y: auto;
    }
    .button-group {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }
    .error {
      color: #e57373;
      font-size: 0.9rem;
      margin-top: 5px;
    }
  `;

  constructor() {
    super();
    this.agents = [];
    this.apiKeys = [];
    this.selectedAgent = '';
    this.domainName = window.location.origin;
    this.apiKey = '';
    this.scriptContent = '';
    this.showPreview = false;
    
    this.fetchApiKeys();
    this.fetchAgents();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    // Ensure preview elements are removed if the component is destroyed
    this._removeGlobalPreview();
  }

  async fetchAgents() {
    try {
      const response = await fetch('/agents/local');
      if (!response.ok) throw new Error('Failed to fetch agents');
      this.agents = await response.json();
    } catch (error) {
      showNotification('error', `Error loading agents: ${error.message}`);
    }
  }

  async fetchApiKeys() {
    try {
      const response = await fetch('/api_keys/list');
      if (!response.ok) throw new Error('Failed to fetch API keys');
      const result = await response.json();
      this.apiKeys = result.data || [];
    } catch (error) {
      showNotification('error', `Error loading API keys: ${error.message}`);
    }
  }

  handleInputChange(event) {
    const { name, value } = event.target;
    this[name] = value;
    if (name === 'selectedAgent' || name === 'domainName' || name === 'apiKey') {
      this.generateScript();
    }
  }

  generateScript() {
    if (!this.selectedAgent || !this.domainName || !this.apiKey) {
      this.scriptContent = '';
      return;
    }
    const config = {
        agentName: this.selectedAgent,
        apiKey: this.apiKey,
        domain: this.domainName,
        position: 'bottom-right'
    };
    const scriptBody = [
        '(function() {',
        '  const config = ' + JSON.stringify(config) + ';',
        '  let iframeLoaded = false;',
        '  function createChatIcon() {',
        '    const icon = document.createElement("div");',
        '    icon.id = "mindroot-chat-icon";',
        '    icon.innerHTML = "&#128172;";',
        '    icon.style.cssText = "position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; background: #2196F3; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); z-index: 10000; font-size: 24px; color: white; transition: all 0.3s ease;";',
        '    icon.addEventListener("click", toggleChat);',
        '    document.body.appendChild(icon);',
        '  }',
        '  function createChatIframe() {',
        '    const container = document.createElement("div");',
        '    container.id = "mindroot-chat-container";',
        '    container.style.cssText = "position: fixed; bottom: 90px; right: 20px; width: 400px; height: 600px; background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); z-index: 10001; display: none; overflow: hidden;";',
        '    const iframe = document.createElement("iframe");',
        '    iframe.style.cssText = "width: 100%; height: 100%; border: none; border-radius: 12px;";',
        '    container.appendChild(iframe);',
        '    document.body.appendChild(container);',
        '  }',
        '  function toggleChat() {',
        '    const container = document.getElementById("mindroot-chat-container");',
        '    const iframe = container.querySelector("iframe");',
        '    if (!iframeLoaded) {',
        '      iframe.src = `${config.domain}/agent/${config.agentName}?api_key=${config.apiKey}&embed=true`;',
        '      iframeLoaded = true;',
        '    }',
        '    container.style.display = (container.style.display === "none" || !container.style.display) ? "block" : "none";',
        '  }',
        '  function init() {',
        '    if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", function() { createChatIcon(); createChatIframe(); }); }',
        '    else { createChatIcon(); createChatIframe(); }',
        '  }',
        '  init();',
        '})();'
    ].join('\n');
    this.scriptContent = [
        '<!-- MindRoot AI Chat Widget -->',
        '<div id="mindroot-chat-widget"></div>',
        '<script>',
        scriptBody,
        '</script>',
        '<!-- End MindRoot AI Chat Widget -->'
    ].join('\n');
  }

  togglePreview() {
    this.showPreview = !this.showPreview;
    if (this.showPreview) {
      this._createGlobalPreview();
    } else {
      this._removeGlobalPreview();
    }
  }

  _createGlobalPreview() {
    this._removeGlobalPreview(); // Clean up any previous instances

    const chatIcon = document.createElement('div');
    chatIcon.id = 'mindroot-preview-chat-icon';
    chatIcon.innerHTML = '<span class="material-icons">chat</span>';
    chatIcon.style.cssText = 'position: fixed; bottom: 20px; right: 20px; width: 60px; height: 60px; background: #2196F3; border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); z-index: 10000; color: white; font-size: 24px;';
    chatIcon.addEventListener('click', () => this._togglePreviewChatWindow());
    document.body.appendChild(chatIcon);
  }

  _togglePreviewChatWindow() {
    let chatContainer = document.getElementById('mindroot-preview-chat-container');
    if (!chatContainer) {
      chatContainer = document.createElement('div');
      chatContainer.id = 'mindroot-preview-chat-container';
      chatContainer.style.cssText = 'position: fixed; bottom: 90px; right: 20px; width: 400px; height: 600px; background: white; border-radius: 12px; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); z-index: 10001; display: block; overflow: hidden;';
      
      const iframe = document.createElement('iframe');
      iframe.style.cssText = 'width: 100%; height: 100%; border: none; border-radius: 12px;';
      iframe.src = `${this.domainName}/agent/${this.selectedAgent}?api_key=${this.apiKey}&embed=true`;
      chatContainer.appendChild(iframe);
      document.body.appendChild(chatContainer);
    } else {
      chatContainer.style.display = chatContainer.style.display === 'none' ? 'block' : 'none';
    }
  }

  _removeGlobalPreview() {
    const chatIcon = document.getElementById('mindroot-preview-chat-icon');
    if (chatIcon) chatIcon.remove();
    const chatContainer = document.getElementById('mindroot-preview-chat-container');
    if (chatContainer) chatContainer.remove();
  }

  _render() {
    return html`
      <div class="api-key-script">
        <div class="section">
          <h3>Chat Widget Generator</h3>
          <p>Generate an embeddable chat widget script for your website.</p>
          
          <div class="form-group">
            <label for="selectedAgent">Select Agent:</label>
            <select name="selectedAgent" @change=${this.handleInputChange} .value=${this.selectedAgent}>
              <option value="">Choose an agent...</option>
              ${this.agents.map(agent => html`<option value="${agent.name}">${agent.name}</option>`)}
            </select>
          </div>

          <div class="form-group">
            <label for="domainName">Domain Name:</label>
            <input type="text" name="domainName" .value=${this.domainName} @input=${this.handleInputChange} placeholder="https://your-domain.com">
          </div>

          <div class="form-group">
            <label for="apiKey">Select API Key:</label>
            <select name="apiKey" @change=${this.handleInputChange} .value=${this.apiKey}>
              <option value="">Choose an API key...</option>
              ${this.apiKeys.map(key => html`<option value="${key.key}">${key.description || key.key.substring(0, 8)}...</option>`)}
            </select>
            ${!this.apiKey ? html`<div class="error">An API key is required.</div>` : ''}
          </div>

          <div class="button-group">
            <button @click=${this.generateScript}>Generate Script</button>
            <button class="secondary" @click=${this.togglePreview} ?disabled=${!this.scriptContent}>
              ${this.showPreview ? 'Hide Preview' : 'Show Preview'}
            </button>
          </div>
        </div>

        ${this.scriptContent ? html`
          <div class="section">
            <h3>Generated Script</h3>
            <div class="script-preview">${this.scriptContent}</div>
            <div class="button-group">
              <button @click=${() => this.copyScript()}>Copy Script</button>
              <button class="secondary" @click=${() => this.saveScript()}>Download Script</button>
            </div>
          </div>
        ` : ''}

        ${this.showPreview ? html`
          <div class="section">
            <h3>Live Preview</h3>
            <p>A live preview of the chat widget is now active on this page in the bottom-right corner. Click 'Hide Preview' to remove it.</p>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('api-key-script', ApiKeyScript);
