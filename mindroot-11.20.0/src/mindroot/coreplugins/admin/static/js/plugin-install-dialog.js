import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class PluginInstallDialog extends BaseEl {
  static properties = {
    isOpen: { type: Boolean },
    pluginName: { type: String },
    installSource: { type: String },
    output: { type: Array },
    isComplete: { type: Boolean },
    hasError: { type: Boolean },
    autoClose: { type: Boolean }
  };

  static styles = css`
    .dialog-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }

    .dialog-backdrop.open {
      opacity: 1;
      pointer-events: auto;
    }

    .dialog {
      background: rgb(15, 15, 30);
      border-radius: 8px;
      width: 95%;
      max-width: 1200px;
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      transform: translateY(20px);
      transition: transform 0.3s ease;
    }

    .dialog-backdrop.open .dialog {
      transform: translateY(0);
    }

    .dialog-header {
      padding: 1rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .dialog-title {
      font-size: 1.2rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .dialog-title .material-icons {
      font-size: 1.2rem;
    }

    .close-button {
      background: none;
      border: none;
      color: rgba(255, 255, 255, 0.7);
      cursor: pointer;
      font-size: 1.5rem;
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .close-button:hover {
      color: white;
    }

    .dialog-content {
      padding: 1rem;
      overflow-y: auto;
      flex: 1;
    }

    .terminal {
      background: rgb(10, 10, 20);
      border-radius: 4px;
      padding: 1rem;
      font-family: monospace;
      /* white-space: pre-wrap; */
      font-size: 0.9rem;
      overflow-x: auto;
      color: #f0f0f0;
      height: 300px;
      overflow-y: auto;
    }

    .terminal-line {
      margin: 0;
      line-height: 1.4;
    }

    .terminal-line.error {
      color: #ff6b6b;
    }

    .terminal-line.warning {
      color: #feca57;
    }

    .terminal-line.success {
      color: #1dd1a1;
    }

    
    .terminal-line.warning {
      color: #feca57;
    }


    .dialog-footer {
      padding: 1rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      justify-content: flex-end;
      gap: 0.5rem;
    }

    .status {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-right: auto;
    }

    .status.success {
      color: #1dd1a1;
    }

    .status.error {
      color: #ff6b6b;
    }

    .status.in-progress {
      color: #feca57;
    }

    .spinner {
      border: 2px solid rgba(255, 255, 255, 0.1);
      border-top: 2px solid #feca57;
      border-radius: 50%;
      width: 16px;
      height: 16px;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    button {
      background: #2a2a40;
      color: white;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    button:hover {
      background: #3a3a50;
    }

    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    button.primary {
      background: #2e86de;
    }

    button.primary:hover {
      background: #54a0ff;
    }
  `;

  constructor() {
    super();
    this.isOpen = false;
    this.pluginName = '';
    this.installSource = '';
    this.output = [];
    this.isComplete = false;
    this.hasError = false;
    this.autoClose = true;
    this.autoCloseTimer = null;
  }

  connectedCallback() {
    super.connectedCallback();
    // Listen for ESC key to close dialog
    this.handleKeyDown = (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    };
    window.addEventListener('keydown', this.handleKeyDown);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    window.removeEventListener('keydown', this.handleKeyDown);
    this.clearAutoCloseTimer();
  }

  open(pluginName, installSource) {
    this.pluginName = pluginName;
    this.installSource = installSource;
    this.output = [];
    this.isComplete = false;
    this.hasError = false;
    this.isOpen = true;
    this.clearAutoCloseTimer();
  }

  close() {
    this.isOpen = false;
    this.clearAutoCloseTimer();
  }

  clearAutoCloseTimer() {
    if (this.autoCloseTimer) {
      clearTimeout(this.autoCloseTimer);
      this.autoCloseTimer = null;
    }
  }

  addOutput(line, type = 'info') {
    // Skip completely empty lines
    if (!line || line.trim() === '') {
      return;
    }
    
    // Debug
    console.log(`Adding output: ${type} - ${JSON.stringify(line)}`);
    
    // Add the line to the output array
    this.output = [...this.output, { text: line, type }];
    // Scroll to bottom
    setTimeout(() => {
      const terminal = this.shadowRoot.querySelector('.terminal');
      if (terminal) {
        terminal.scrollTop = terminal.scrollHeight;
      }
    }, 0);
  }

  setComplete(hasError = false) {
    // Check if there are any actual errors (not just warnings)
    const hasActualErrors = this.output.some(line => line.type === 'error');
    console.log(`setComplete: hasError=${hasError}, hasActualErrors=${hasActualErrors}, output count=${this.output.length}`);
    // Add a final status message
    if (hasError) {
      this.addOutput('Installation failed. See errors above.', 'error');
    } else {
      this.addOutput('✓ Installation completed successfully!', 'success');
    }
    
    this.isComplete = true;
    this.hasError = hasError || hasActualErrors;

    // Auto close after 2 seconds if no error and autoClose is enabled
    if (false && !this.hasError && this.autoClose) {
      this.autoCloseTimer = setTimeout(() => {
        this.close();
      }, 2000);
    }
  }

  handleBackdropClick(e) {
    // Close only if clicking directly on the backdrop, not its children
    if (e.target === e.currentTarget) {
      this.close();
    }
  }

  _render() {
    return html`
      <div class="dialog-backdrop ${this.isOpen ? 'open' : ''}"
           @click=${this.handleBackdropClick}>
        <div class="dialog">
          <div class="dialog-header">
            <div class="dialog-title">
              <span class="material-icons">extension</span>
              Installing ${this.pluginName || 'Plugin'}
            </div>
            <button class="close-button" @click=${this.close}>
              <span class="material-icons">close</span>
            </button>
          </div>
          <div class="dialog-content">
            <div class="terminal">
              ${this.output.map(line => html`
                <div class="terminal-line ${line.type}">${line.text}</div>
              `)}
            </div>
          </div>
          <div class="dialog-footer">
            <div class="status ${this.isComplete ? (this.hasError ? 'error' : 'success') : 'in-progress'}">
              ${this.isComplete
                ? html`<span class="material-icons">${this.hasError ? 'error' : 'check_circle'}</span>
                       <span>${this.hasError ? 'Installation failed' : 'Installation complete'}</span>`
                : html`<div class="spinner"></div>
                       <span>Installing...</span>`
              }
            </div>
            <button @click=${this.close}>
              <span class="material-icons">close</span>
              Close
            </button>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('plugin-install-dialog', PluginInstallDialog);
