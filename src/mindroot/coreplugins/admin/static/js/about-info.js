import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class AboutInfo extends BaseEl {
  static properties = {
    versionInfo: { type: Object },
    loading: { type: Boolean },
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

    .refresh-btn {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-top: 1rem;
    }

    .refresh-btn:hover {
      background: #3a3a50;
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
  `;

  constructor() {
    super();
    this.versionInfo = null;
    this.loading = false;
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

  handleRefresh() {
    this.loadVersionInfo();
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
            <button class="refresh-btn" @click=${this.handleRefresh}>Retry</button>
          ` : this.versionInfo ? html`
            <div class="version-info">
              <div class="label">Commit Hash:</div>
              <div class="value">${this.versionInfo.commit_hash || 'Unknown'}</div>
              
              <div class="label">Last Commit:</div>
              <div class="value">${this.formatDate(this.versionInfo.commit_date)}</div>
              
              <div class="label">Retrieved:</div>
              <div class="value">${this.formatDate(this.versionInfo.retrieved_at)}</div>
            </div>
            <button class="refresh-btn" @click=${this.handleRefresh}>Refresh</button>
          ` : html`
            <div class="error">No version information available</div>
            <button class="refresh-btn" @click=${this.handleRefresh}>Retry</button>
          `}
        </div>
      </div>
    `;
  }
}

customElements.define('about-info', AboutInfo);
