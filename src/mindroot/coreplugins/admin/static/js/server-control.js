import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class ServerControl extends BaseEl {
  static properties = {
    status: { type: String },
    loading: { type: Boolean },
    method: { type: String }
  };

  static styles = css`
    .server-controls {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      padding: 1rem;
      background: rgb(15, 15, 30);
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .buttons {
      display: flex;
      gap: 1rem;
    }

    .control-button {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1.5rem;
      border-radius: 6px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
      cursor: pointer;
      font-size: 1rem;
      transition: all 0.2s ease;
    }

    .control-button:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    .control-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .restart { 
      background: #2196F3;
      border-color: #1976D2;
    }
    
    .restart:hover {
      background: #1976D2;
    }

    .stop { 
      background: #f44336;
      border-color: #d32f2f;
    }

    .stop:hover {
      background: #d32f2f;
    }
    
    .status-message {
      margin-top: 1rem;
      padding: 1rem;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.05);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .status-message.error {
      background: rgba(244, 67, 54, 0.1);
      border: 1px solid rgba(244, 67, 54, 0.2);
    }

    .status-message.success {
      background: rgba(76, 175, 80, 0.1);
      border: 1px solid rgba(76, 175, 80, 0.2);
    }

    .method-tag {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      font-size: 0.85rem;
      background: rgba(255, 255, 255, 0.1);
      margin-left: 0.5rem;
    }

    @keyframes spin {
      100% { transform: rotate(360deg); }
    }

    .loading .material-icons {
      animation: spin 1s linear infinite;
    }
  `;

  constructor() {
    super();
    this.status = '';
    this.loading = false;
    this.method = '';
  }

  async handleRestart() {
    if (!confirm('Are you sure you want to restart the server?')) return;
    
    this.loading = true;
    this.status = 'Initiating server restart...';
    
    try {
      const response = await fetch('/admin/server/restart', {
        method: 'POST',
      });
      const result = await response.json();
      
      if (result.success) {
        this.status = result.message;
        this.method = result.method;
        
        // For PM2 and mindroot methods, we'll reload after a delay
        if (result.method === 'pm2' || result.method === 'mindroot') {
          setTimeout(() => {
            this.status = 'Attempting to reconnect...';
            window.location.reload();
          }, 5000);
        }
      } else {
        throw new Error(`${result.message}${result.method ? ` (${result.method})` : ''}`);
      }
    } catch (error) {
      this.status = 'Failed to restart server: ' + error.message;
      this.method = '';
    } finally {
      this.loading = false;
    }
  }

  async handleStop() {
    if (!confirm('Are you sure you want to stop the server? You will need to restart it manually unless using PM2.')) return;
    
    this.loading = true;
    this.status = 'Initiating server shutdown...';
    
    try {
      const response = await fetch('/admin/server/stop', {
        method: 'POST',
      });
      const result = await response.json();
      
      if (result.success) {
        this.status = result.message;
      } else {
        throw new Error(result.message);
      }
    } catch (error) {
      this.status = 'Failed to stop server: ' + error.message;
    } finally {
      this.loading = false;
    }
  }

  _render() {
    return html`
      <div class="server-controls">
        <div class="buttons">
          <button 
            class="control-button restart" 
            @click=${this.handleRestart}
            ?disabled=${this.loading}>
            <span class="material-icons">${this.loading ? 'refresh' : 'restart_alt'}</span>
            Restart Server
          </button>
          <button 
            class="control-button stop" 
            @click=${this.handleStop}
            ?disabled=${this.loading}>
            <span class="material-icons">power_settings_new</span>
            Stop Server
          </button>
        </div>
        ${this.status ? html`
          <div class="status-message ${this.loading ? 'loading' : ''} ${this.status.includes('Failed') ? 'error' : 'success'}">
            <span class="material-icons">
              ${this.loading ? 'refresh' : this.status.includes('Failed') ? 'error' : 'info'}
            </span>
            ${this.status}
            ${this.method ? html`
              <span class="method-tag">
                <span class="material-icons">${this.method === 'pm2' ? 'cloud_queue' : 'terminal'}</span>
                ${this.method}
              </span>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('server-control', ServerControl);
