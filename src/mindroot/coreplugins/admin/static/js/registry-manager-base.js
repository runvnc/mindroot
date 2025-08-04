import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class RegistryManagerBase extends BaseEl {
  static properties = {
    isLoggedIn: { type: Boolean },
    searchResults: { type: Array },
    registryUrl: { type: String },
    currentUser: { type: Object },
    authToken: { type: String },
    searchQuery: { type: String },
    selectedCategory: { type: String },
    loading: { type: Boolean },
    error: { type: String },
    stats: { type: Object },
    publishSuccess: { type: String },
    showPublishForm: { type: Boolean },
    localPlugins: { type: Array },
    localAgents: { type: Array },
    agentOwnership: { type: Object },
    toasts: { type: Array },
    activeTab: { type: String },
    showRegisterForm: { type: Boolean },
    installRecommendedPlugins: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .registry-manager {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      gap: 20px;
      padding: 1rem;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section h3, .section h4 {
      margin-top: 0;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .settings-section {
      margin-bottom: 1rem;
    }

    .settings-section summary {
      cursor: pointer;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #fff;
    }

    .settings-section summary:hover {
      background: rgba(0, 0, 0, 0.3);
    }

    .help-text {
      font-size: 0.8rem;
      color: #999;
      margin-top: 0.5rem;
    }

    .registry-url-display {
      font-size: 0.8rem;
      color: #999;
      margin-bottom: 0.5rem;
    }

    .login-form, .search-form, .publish-form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-width: 400px;
    }

    .form-row {
      display: flex;
      gap: 1rem;
      align-items: center;
      flex-wrap: wrap;
    }

    .form-row label {
      color: #fff;
      min-width: 100px;
    }

    input, select, textarea {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      flex: 1;
      min-width: 200px;
    }

    input:focus, select:focus, textarea:focus {
      outline: none;
      border-color: #4a9eff;
    }

    button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      white-space: nowrap;
    }

    button:hover {
      background: #3a3a50;
    }

    button.primary {
      background: #4a9eff;
    }

    button.primary:hover {
      background: #3a8eef;
    }

    button.success {
      background: #28a745;
      color: #fff !important;
    }

    button.success:hover {
      background: #218838;
      color: #fff !important;
    }

    .search-results {
      display: grid;
      gap: 1rem;
      margin-top: 1rem;
    }

    .result-item {
      background: rgba(0, 0, 0, 0.2);
      padding: 1rem;
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .result-item {
      display: flex;
      align-items: flex-start;
      gap: 1rem;
    }

    .result-avatar {
      flex-shrink: 0;
    }

    .agent-avatar-large {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid rgba(74, 158, 255, 0.3);
      background: rgba(0, 0, 0, 0.2);
    }

    .result-content {
      flex: 1;
      min-width: 0;
    }

    .agent-name-with-face {
      font-size: 1.2rem;
      font-weight: bold;
      color: #4a9eff;
      margin: 0;
    }

    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.5rem;
    }

    .result-title {
      font-weight: bold;
      color: #4a9eff;
      margin: 0;
    }

    .result-version {
      background: rgba(74, 158, 255, 0.2);
      color: #4a9eff;
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-size: 0.8rem;
    }

    .result-description {
      color: #ccc;
      margin: 0.5rem 0;
    }

    .result-meta {
      display: flex;
      gap: 1rem;
      font-size: 0.8rem;
      color: #999;
      margin: 0.5rem 0;
    }

    .result-tags {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin: 0.5rem 0;
    }

    .tag {
      background: rgba(255, 255, 255, 0.1);
      padding: 0.2rem 0.5rem;
      border-radius: 3px;
      font-size: 0.7rem;
    }

    .result-actions {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 1rem;
      margin: 1rem 0;
    }

    .stat-card {
      background: rgba(0, 0, 0, 0.2);
      padding: 1rem;
      border-radius: 4px;
      text-align: center;
    }

    .stat-number {
      font-size: 2rem;
      font-weight: bold;
      color: #4a9eff;
    }

    .stat-label {
      color: #ccc;
      font-size: 0.9rem;
    }

    /* Toast notifications */
    .toast-container {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 1000;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .toast {
      background: rgba(0, 0, 0, 0.9);
      color: white !important;
      padding: 12px 20px;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      max-width: 400px;
      word-wrap: break-word;
      animation: slideIn 0.3s ease-out;
      border-left: 4px solid #4a9eff;
    }

    .toast.success {
      border-left-color: #28a745;
      background: rgba(40, 167, 69, 0.9);
      color: white !important;
    }

    .toast.error {
      border-left-color: #dc3545;
      background: rgba(220, 53, 69, 0.9);
      color: white !important;
    }

    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }

    .error {
      background: rgba(220, 53, 69, 0.2);
      color: #dc3545;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }

    .success {
      background: rgba(40, 167, 69, 0.2);
      color: #28a745;
      padding: 0.5rem;
      border-radius: 4px;
      margin: 0.5rem 0;
    }

    .loading {
      text-align: center;
      color: #ccc;
      padding: 2rem;
    }

    .user-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;
      flex-wrap: wrap;
      gap: 1rem;
    }

    .tabs {
      display: flex;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }

    .tab {
      padding: 0.5rem 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
    }

    .tab.active {
      background: #4a9eff;
    }

    .tab:hover {
      background: rgba(74, 158, 255, 0.3);
    }

    .auth-toggle {
      text-align: center;
      margin-top: 1rem;
    }

    .category-tabs {
      display: flex;
      gap: 0.5rem;
      margin-top: 1rem;
      flex-wrap: wrap;
    }

    .category-tab {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      color: #ccc;
      font-size: 0.9rem;
    }

    .category-tab:hover {
      background: rgba(74, 158, 255, 0.2);
      border-color: rgba(74, 158, 255, 0.3);
      color: #fff;
    }

    .category-tab.active {
      background: #4a9eff;
      border-color: #4a9eff;
      color: #fff;
    }

    .category-tab .material-icons {
      font-size: 1.1rem;
    }

    .no-results {
      text-align: center;
      padding: 2rem;
      color: #999;
      background: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
    }

    .semantic-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      background: rgba(156, 39, 176, 0.2);
      color: #9c27b0;
      padding: 0.25rem 0.5rem;
      border-radius: 12px;
      font-size: 0.75rem;
      margin-bottom: 0.5rem;
      border: 1px solid rgba(156, 39, 176, 0.3);
    }

    .oauth-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      background: rgba(255, 152, 0, 0.2);
      color: #ff9800;
      padding: 0.25rem 0.5rem;
      border-radius: 12px;
      font-size: 0.75rem;
      margin-left: 0.5rem;
      border: 1px solid rgba(255, 152, 0, 0.3);
    }

    .oauth-badge .material-icons {
      font-size: 0.9rem;
    }

    .oauth-status {
      display: inline-flex;
      align-items: center;
      margin-left: 0.5rem;
    }

    .oauth-status.needs-auth {
      color: #ffc107;
    }

    .oauth-status .material-icons {
      font-size: 1rem;
    }

    .installed-badge {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      color: #28a745;
    }
  `;

  constructor() {
    super();
    this.isLoggedIn = false;
    this.searchResults = [];
    this.registryUrl = this.loadRegistryUrl();
    this.currentUser = null;
    this.authToken = localStorage.getItem('registry_token');
    this.searchQuery = '';
    this.selectedCategory = 'all';
    this.loading = false;
    this.error = '';
    this.stats = {};
    this.publishSuccess = '';
    this.toasts = [];
    this.showPublishForm = false;
    this.localPlugins = [];
    this.localAgents = [];
    this.agentOwnership = null;
    this.activeTab = 'search';
    this.showRegisterForm = false;
    // Automatically install recommended plugins when installing agents
    this.installRecommendedPlugins = true;
    
    this.checkAuthStatus();
    this.loadStats();
    this.loadLocalContent();
  }

  loadRegistryUrl() {
    return localStorage.getItem('registry_url') || 
           (typeof window !== 'undefined' && window.MR_REGISTRY_URL) || 
           'https://registry.mindroot.io';
  }

  updateRegistryUrl(newUrl) {
    this.registryUrl = newUrl;
    localStorage.setItem('registry_url', newUrl);
    this.logout();
    this.loadStats();
    this.requestUpdate();
  }

  async testConnection() {
    try {
      const response = await fetch(`${this.registryUrl}/stats`);
      if (response.ok) {
        this.error = '';
        await this.loadStats();
        const originalError = this.error;
        this.error = 'Connection successful!';
        this.requestUpdate();
        setTimeout(() => {
          this.error = originalError;
          this.requestUpdate();
        }, 2000);
      } else {
        this.error = `Connection failed: ${response.status}`;
      }
    } catch (error) {
      this.error = `Connection failed: ${error.message}`;
    }
    this.requestUpdate();
  }

  async register(username, email, password) {
    this.loading = true;
    
    try {
      const response = await fetch(`${this.registryUrl}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username,
          email: email,
          password: password
        })
      });
      
      if (response.ok) {
        this.showToast('Registration successful! You can now log in.', 'success');
        this.showRegisterForm = false;
    // Automatically install recommended plugins when installing agents
    this.installRecommendedPlugins = true;
      } else {
        const errorData = await response.json();
        this.showToast(errorData.detail || 'Registration failed', 'error');
      }
    } catch (error) {
      this.showToast('Network error: ' + error.message, 'error');
    }
    
    this.loading = false;
    this.requestUpdate();
  }

  showToast(message, type = 'info', duration = 5000) {
    const toast = {
      id: Date.now() + Math.random(),
      message,
      type,
      duration
    };
    
    this.toasts = [...this.toasts, toast];
    this.requestUpdate();
    
    // Auto-remove toast after duration
    setTimeout(() => {
      this.removeToast(toast.id);
    }, duration);
  }

  removeToast(toastId) {
    this.toasts = this.toasts.filter(toast => toast.id !== toastId);
    this.requestUpdate();
  }

  renderToasts() {
    if (this.toasts.length === 0) return '';
    
    return html`
      <div class="toast-container">
        ${this.toasts.map(toast => html`
          <div class="toast ${toast.type}" @click=${() => this.removeToast(toast.id)}>
            ${toast.message}
          </div>
        `)}
      </div>
    `;
  }
}

export { RegistryManagerBase };
