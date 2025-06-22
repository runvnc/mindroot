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
    showPublishForm: { type: Boolean },
    localPlugins: { type: Array },
    localAgents: { type: Array },
    activeTab: { type: String }
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

    .section h3 {
      margin-top: 0;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
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
    }

    input, select, textarea {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      flex: 1;
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
    }

    button.success:hover {
      background: #218838;
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
  `;

  constructor() {
    super();
    this.isLoggedIn = false;
    this.searchResults = [];
    this.registryUrl = 'http://localhost:8000';
    this.currentUser = null;
    this.authToken = localStorage.getItem('registry_token');
    this.searchQuery = '';
    this.selectedCategory = 'all';
    this.loading = false;
    this.error = '';
    this.stats = {};
    this.showPublishForm = false;
    this.localPlugins = [];
    this.localAgents = [];
    this.activeTab = 'search';
    
    this.checkAuthStatus();
    this.loadStats();
    this.loadLocalContent();
  }
}

export { RegistryManagerBase };
