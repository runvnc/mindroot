import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class AboutInfo extends BaseEl {
  static properties = {
    versionInfo: { type: Object },
    loading: { type: Boolean },
    updating: { type: Boolean },
    updateResult: { type: Object },
    error: { type: String }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .about-container {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 800px;
      margin: 0 auto;
      gap: 20px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1.5rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section h2 {
      margin: 0 0 1rem 0;
      color: #fff;
      font-size: 1.2rem;
      font-weight: 500;
    }

    .version-info {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 0.5rem 1rem;
      align-items: center;
    }

    .label {
      font-weight: 500;
      color: rgba(255, 255, 255, 0.8);
    }

    .value {
      font-family: monospace;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      color: #fff;
      word-break: break-all;
    }

    .loading {
      text-align: center;
      padding: 2rem;
      color: rgba(255, 255, 255, 0.6);
    }

    .error {
      color: #ff6b6b;
      background: rgba(255, 107, 107, 0.1);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(255, 107, 107, 0.2);
    }

    .success {
      color: #51cf66;
      background: rgba(81, 207, 102, 0.1);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(81, 207, 102, 0.2);
    }

    .warning {
      color: #ffd43b;
      background: rgba(255, 212, 59, 0.1);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(255, 212, 59, 0.2);
    }

    .info {
      color: #74c0fc;
      background: rgba(116, 192, 252, 0.1);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(116, 192, 252, 0.2);
    }

    .btn {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-top: 1rem;
      margin-right: 0.5rem;
    }

    .btn:hover:not(:disabled) {
      background: #3a3a50;
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .btn.update {
      background: #2a4a2a;
    }

    .btn.update:hover:not(:disabled) {
      background: #3a5a3a;
    }

    .logo-section {
      text-align: center;
    }

    .logo-section img {
      max-width: 200px;
      height: auto;
    }

    .title {
      font-size: 2rem;
      font-weight: bold;
      color: #fff;
      margin: 1rem 0;
    }

    .description {
      color: rgba(255, 255, 255, 0.8);
      line-height: 1.6;
    }

    .update-output {
      background: rgba(0, 0, 0, 0.3);
      padding: 1rem;
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.9rem;
      white-space: pre-wrap;
      max-height: 300px;
      overflow-y: auto;
      margin-top: 1rem;
    }

    .button-group {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .restart-notice {
      margin-top: 1rem;
    }

    .restart-notice p {
      margin: 0 0 0.5rem 0;
    }

    .tab-link {
      color: #74c0fc;
      text-decoration: underline;
      cursor: pointer;
    }

    .tab-link:hover {
      color: #91d5ff;
    }
  `;

  constructor() {
    super();
    this.versionInfo = null;
    this.loading = false;
    this.updating = false;
    this.updateResult = null;
    this.error = null;
    this.loadVersionInfo();
  }

  async loadVersionInfo() {
    this.loading = true;
    this.error = null;
    
    try {
      // First try to get git info and update version.txt
      const response = await fetch('/admin/get-version-info', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        this.versionInfo = result;
      } else {
        throw new Error('Failed to get version info');
      }
    } catch (error) {
      console.error('Error loading version info:', error);
      this.error = 'Failed to load version information';
    } finally {
      this.loading = false;
    }
  }

  async handleUpdate() {
    this.updating = true;
    this.updateResult = null;
    this.error = null;
    
    try {
      const response = await fetch('/admin/update-mindroot', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        this.updateResult = result;
        
        // If successful, refresh version info after a short delay
        if (result.success) {
          setTimeout(() => {
            this.loadVersionInfo();
          }, 2000);
        }
      } else {
        throw new Error('Failed to update MindRoot');
      }
    } catch (error) {
      console.error('Error updating MindRoot:', error);
      this.error = 'Failed to update MindRoot';
    } finally {
      this.updating = false;
    }
  }

  handleRefresh() {
    this.loadVersionInfo();
  }

  switchToServerTab() {
    // Find and click the Server Control tab
    const serverTab = document.querySelector('details[data-tab="server"] summary');
    if (serverTab) {
      // Close current tab if it's open
      const currentTab = document.querySelector('details[open]');
      if (currentTab && currentTab !== serverTab.parentElement) {
        currentTab.removeAttribute('open');
      }
      // Open server tab
      serverTab.parentElement.setAttribute('open', '');
      serverTab.scrollIntoView({ behavior: 'smooth' });
    }
  }

  formatDate(dateString) {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  }

  _render() {
    return html`
      <div class="about-container">
        <div class="section logo-section">
          <img src="/admin/static/logo.png" alt="MindRoot Logo" />
          <div class="title">MindRoot</div>
          <div class="description">
            Advanced AI agent framework with modular plugin architecture
          </div>
        </div>

        <div class="section">
          <h2>Version Information</h2>
          
          ${this.loading ? html`
            <div class="loading">Loading version information...</div>
          ` : this.error ? html`
            <div class="error">${this.error}</div>
            <button class="btn" @click=${this.handleRefresh}>Retry</button>
          ` : this.versionInfo ? html`
            <div class="version-info">
              <div class="label">Commit Hash:</div>
              <div class="value">${this.versionInfo.commit_hash || 'Unknown'}</div>
              
              <div class="label">Last Commit:</div>
              <div class="value">${this.formatDate(this.versionInfo.commit_date)}</div>
              
              <div class="label">Retrieved:</div>
              <div class="value">${this.formatDate(this.versionInfo.retrieved_at)}</div>
            </div>
            
            <div class="button-group">
              <button class="btn" @click=${this.handleRefresh}>Refresh</button>
              <button 
                class="btn update" 
                @click=${this.handleUpdate}
                ?disabled=${this.updating}
              >
                ${this.updating ? 'Updating...' : 'Update MindRoot'}
              </button>
            </div>
          ` : html`
            <div class="error">No version information available</div>
            <button class="btn" @click=${this.handleRefresh}>Retry</button>
          `}
        </div>

        ${this.updateResult ? html`
          <div class="section">
            <h2>Update Result</h2>
            
            ${this.updateResult.success ? html`
              <div class="success">
                ${this.updateResult.message}
              </div>
              
              <div class="restart-notice">
                <div class="info">
                  <p><strong>Restart Required:</strong> To use the updated version, you need to restart the MindRoot server.</p>
                  <p>You can restart the server using the <span class="tab-link" @click=${this.switchToServerTab}>Server Control</span> tab.</p>
                </div>
              </div>
            ` : html`
              <div class="error">
                ${this.updateResult.message}
                ${this.updateResult.error ? html`<br><strong>Error:</strong> ${this.updateResult.error}` : ''}
              </div>
            `}
            
            ${this.updateResult.output ? html`
              <div class="update-output">${this.updateResult.output}</div>
            ` : ''}
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('about-info', AboutInfo);
