import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';

class PublishButton extends LitElement {
  static properties = {
    indexName: { type: String },
    loading: { type: Boolean },
    downloadUrl: { type: String },
    error: { type: String }
  };

  static styles = css`
    :host {
      display: inline-block;
    }

    .publish-button {
      background: #27ae60;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .publish-button:hover {
      background: #2ecc71;
    }

    .publish-button:disabled {
      background: #95a5a6;
      cursor: not-allowed;
    }

    .loading-spinner {
      display: inline-block;
      width: 16px;
      height: 16px;
      border: 2px solid #fff;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s linear infinite;
    }

    .download-link {
      color: #3498db;
      text-decoration: none;
      margin-left: 1rem;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .download-link:hover {
      text-decoration: underline;
    }

    .error-message {
      color: #e74c3c;
      margin-left: 1rem;
      font-size: 0.9rem;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;

  constructor() {
    super();
    this.loading = false;
    this.downloadUrl = '';
    this.error = '';
  }

  async handlePublish() {
    if (!this.indexName || this.loading) return;

    this.loading = true;
    this.error = '';
    this.downloadUrl = '';

    try {
      const response = await fetch(`/index/publish/${this.indexName}`, {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        // The URL will now be a path like /index/published/name-timestamp.zip
        this.downloadUrl = result.zip_file;
        this.dispatchEvent(new CustomEvent('publish-success', {
          detail: { message: result.message, zipFile: result.zip_file }
        }));
      } else {
        this.error = result.message || 'Failed to publish index';
      }
    } catch (error) {
      console.error('Error publishing index:', error);
      this.error = 'Failed to publish index';
    } finally {
      this.loading = false;
    }
  }

  render() {
    return html`
      <div>
        <button class="publish-button" 
                ?disabled=${this.loading || !this.indexName}
                @click=${this.handlePublish}>
          ${this.loading ? html`
            <div class="loading-spinner"></div>
            <span>Publishing...</span>
          ` : html`
            <span>Publish Index</span>
          `}
        </button>

        ${this.downloadUrl ? html`
          <a href=${this.downloadUrl} class="download-link" download>
            <span>Download ZIP</span>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 12l-4-4h2.5V3h3v5H12L8 12z"/>
              <path d="M14 13v1H2v-1h12z"/>
            </svg>
          </a>
        ` : ''}

        ${this.error ? html`
          <span class="error-message">${this.error}</span>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('publish-button', PublishButton);
