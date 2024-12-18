import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class GithubImport extends BaseEl {
  static properties = {
    scope: { type: String },
    loading: { type: Boolean },
    githubRepo: { type: String },
    githubTag: { type: String }
  };

  static styles = css`
    :host {
      display: block;
      margin: 20px 0;
    }

    .github-import {
      padding: 15px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
    }

    h3 {
      margin-bottom: 15px;
      font-size: 1.1em;
      color: #f0f0f0;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .github-import-form {
      display: flex;
      gap: 10px;
      align-items: center;
    }

    input {
      flex: 1;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }

    input:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }

    .btn {
      padding: 8px 16px;
      background: transparent;
      border: 1px solid #2196F3;
      color: #2196F3;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.95rem;
      transition: all 0.2s;
      white-space: nowrap;
    }

    .btn:hover {
      background: rgba(33, 150, 243, 0.1);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `;

  constructor() {
    super();
    this.loading = false;
    this.githubRepo = '';
    this.githubTag = '';
  }

  async handleGitHubImport() {
    if (!this.githubRepo) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: 'GitHub repository is required'
      }));
      return;
    }

    try {
      this.loading = true;
      const response = await fetch('/import-github-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_path: this.githubRepo,
          scope: this.scope,
          tag: this.githubTag || undefined
        })
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('agent-installed', {
          detail: { name: this.githubRepo.split('/')[1] }
        }));
        this.githubRepo = '';
        this.githubTag = '';
      } else {
        throw new Error(result.message || 'Failed to import from GitHub');
      }
    } catch (error) {
      this.dispatchEvent(new CustomEvent('error', {
        detail: `Error importing from GitHub: ${error.message}`
      }));
    } finally {
      this.loading = false;
    }
  }

  _render() {
    return html`
      <div class="github-import">
        <h3>
          <span class="material-icons">code</span>
          Import from GitHub
        </h3>
        <div class="github-import-form">
          <input type="text"
                 placeholder="owner/repository"
                 .value=${this.githubRepo}
                 @input=${e => this.githubRepo = e.target.value}>
          <input type="text"
                 placeholder="tag (optional)"
                 .value=${this.githubTag}
                 @input=${e => this.githubTag = e.target.value}>
          <button class="btn"
                  @click=${this.handleGitHubImport}
                  ?disabled=${this.loading || !this.githubRepo}>
            Import from GitHub
          </button>
        </div>
      </div>
    `;
  }
}

customElements.define('github-import', GithubImport);
