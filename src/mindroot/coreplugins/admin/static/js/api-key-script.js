import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import showNotification from './notification.js';

class ApiKeyScript extends BaseEl {
  static properties = {
    agents: { type: Array },
    selectedAgent: { type: String },
    domainName: { type: String },
    apiKey: { type: String },
    scriptContent: { type: String },
    showPreview: { type: Boolean }
  };

  static styles = css`
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

    input[type="text"]:focus,
    select:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
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

    button.secondary:hover {
      background: #3a3a50;
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

    .preview-section {
      margin-top: 20px;
    }

    .preview-iframe {
      width: 100%;
      height: 500px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      background: white;
    }

    .chat-icon {
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      background: #2196F3;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      z-index: 1000;
      transition: all 0.3s ease;
    }

    .chat-icon:hover {
      background: #1976D2;
      transform: scale(1.1);
    }

    .chat-icon .material-icons {
      color: white;
      font-size: 24px;
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
    this.selectedAgent = '';
    this.domainName = window.location.origin;
    this.apiKey = '';
    this.scriptContent = '';
    this.showPreview = false;
    
    this.fetchAgents();
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

    const script = `<!-- MindRoot AI Chat Widget -->
<div id="mindroot-chat-widget"></div>
<script>
(function() {
  // Configuration
  const config = {
    agentName: '${this.selectedAgent}',
    apiKey: '${this.apiKey}',
    domain: '${this.domainName}',
    position: 'bottom-right'
  };

  // Create chat icon
  function createChatIcon() {
    const icon = document.createElement('div');
    icon.id = 'mindroot-chat-icon';
    icon.innerHTML = '💬';
    icon.style.cssText = \`
      position: fixed;
      bottom: 20px;
      right: 20px;
      width: 60px;
      height: 60px;
      background: #2196F3;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      z-index: 10000;
      font-size: 24px;
      transition: all 0.3s ease;
    \`;
    
    icon.addEventListener('click', toggleChat);
    icon.addEventListener('mouseenter', function() {
      this.style.background = '#1976D2';
      this.style.transform = 'scale(1.1)';
    });
    icon.addEventListener('mouseleave', function() {
      this.style.background = '#2196F3';
      this.style.transform = 'scale(1)';
    });
    
    document.body.appendChild(icon);
    return icon;
  }

  // Create chat iframe
  function createChatIframe() {
    const container = document.createElement('div');
    container.id = 'mindroot-chat-container';
    container.style.cssText = \`
      position: fixed;
      bottom: 90px;
      right: 20px;
      width: 400px;
      height: 600px;
      background: white;
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      z-index: 10001;
      display: none;
      overflow: hidden;
    \`;
    
    const iframe = document.createElement('iframe');
    iframe.src = \`\${config.domain}/agent/\${config.agentName}?api_key=\${config.apiKey}&embed=true\`;
    iframe.style.cssText = \`
      width: 100%;
      height: 100%;
      border: none;
      border-radius: 12px;
    \`;
    
    container.appendChild(iframe);
    document.body.appendChild(container);
    return container;
  }

  // Toggle chat visibility
  function toggleChat() {
    const container = document.getElementById('mindroot-chat-container');
    if (container.style.display === 'none' || !container.style.display) {
      container.style.display = 'block';
    } else {
      container.style.display = 'none';
    }
  }

  // Initialize widget
  function init() {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        createChatIcon();
        createChatIframe();
      });
    } else {
      createChatIcon();
      createChatIframe();
    }
  }

  init();
})();
</script>`;

    this.scriptContent = script;
  }

  async saveScript() {
    if (!this.scriptContent) {
      showNotification('error', 'Please generate a script first');
      return;
    }

    try {
      const filename = `mindroot-chat-${this.selectedAgent}-${Date.now()}.html`;
      const blob = new Blob([this.scriptContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      showNotification('success', `Script saved as ${filename}`);
    } catch (error) {
      showNotification('error', `Error saving script: ${error.message}`);
    }
  }

  copyScript() {
    if (!this.scriptContent) {
      showNotification('error', 'Please generate a script first');
      return;
    }

    navigator.clipboard.writeText(this.scriptContent).then(() => {
      showNotification('success', 'Script copied to clipboard');
    }).catch(() => {
      showNotification('error', 'Failed to copy script');
    });
  }

  togglePreview() {
    this.showPreview = !this.showPreview;
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
              ${this.agents.map(agent => html`
                <option value="${agent.name}">${agent.name}</option>
              `)}
            </select>
          </div>

          <div class="form-group">
            <label for="domainName">Domain Name:</label>
            <input 
              type="text" 
              name="domainName" 
              .value=${this.domainName}
              @input=${this.handleInputChange}
              placeholder="https://your-domain.com"
            >
          </div>

          <div class="form-group">
            <label for="apiKey">API Key:</label>
            <input 
              type="text" 
              name="apiKey" 
              .value=${this.apiKey}
              @input=${this.handleInputChange}
              placeholder="Enter your API key"
            >
            ${!this.apiKey ? html`
              <div class="error">API key is required. You can generate one in the API Keys section.</div>
            ` : ''}
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
              <button @click=${this.copyScript}>Copy Script</button>
              <button class="secondary" @click=${this.saveScript}>Download Script</button>
            </div>
          </div>
        ` : ''}

        ${this.showPreview && this.selectedAgent && this.apiKey ? html`
          <div class="section preview-section">
            <h3>Live Preview</h3>
            <p>This shows how the chat widget will appear on your website:</p>
            <iframe 
              class="preview-iframe"
              src="${this.domainName}/agent/${this.selectedAgent}?api_key=${this.apiKey}&embed=true"
            ></iframe>
            
            <!-- Demo chat icon -->
            <div class="chat-icon" @click=${() => showNotification('info', 'This is a preview of the chat icon that will appear on your website')}>
              <span class="material-icons">chat</span>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('api-key-script', ApiKeyScript);
