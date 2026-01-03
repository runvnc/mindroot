import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

const RECENT_MODELS_KEY = 'mindroot_recent_models';
const MAX_RECENT = 5;

class ModelSelector extends BaseEl {
  static properties = {
    serviceName: { type: String, attribute: 'service-name' },
    providers: { type: Object },
    selectedValue: { type: String, attribute: 'selected-value' },
    isOpen: { type: Boolean },
    searchTerm: { type: String },
    recentModels: { type: Array }
  };

  static styles = css`
    :host {
      display: block;
      position: relative;
      width: 100%;
    }

    .selector-container {
      position: relative;
    }

    .selected-display {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      cursor: pointer;
      font-size: 0.95rem;
      min-height: 20px;
    }

    .selected-display:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .selected-display.open {
      border-color: #2196F3;
      border-bottom-left-radius: 0;
      border-bottom-right-radius: 0;
    }

    .selected-text {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .selected-provider {
      color: #888;
      font-size: 0.85rem;
      margin-right: 8px;
    }

    .dropdown-arrow {
      color: #888;
      transition: transform 0.2s;
    }

    .dropdown-arrow.open {
      transform: rotate(180deg);
    }

    .dropdown {
      position: absolute;
      top: 100%;
      left: 0;
      right: 0;
      background: #1a1a1a;
      border: 1px solid #2196F3;
      border-top: none;
      border-radius: 0 0 6px 6px;
      max-height: 350px;
      overflow-y: auto;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .search-box {
      padding: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      position: sticky;
      top: 0;
      background: #1a1a1a;
    }

    .search-input {
      width: 100%;
      padding: 8px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: #f0f0f0;
      font-size: 0.9rem;
      box-sizing: border-box;
    }

    .search-input:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.3);
    }

    .section-header {
      padding: 8px 12px;
      background: rgba(33, 150, 243, 0.15);
      color: #64b5f6;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      position: sticky;
      top: 49px;
    }

    .provider-header {
      padding: 6px 12px;
      background: rgba(255, 255, 255, 0.08);
      color: #aaa;
      font-size: 0.85rem;
      font-weight: 500;
    }

    .model-option {
      padding: 8px 12px 8px 24px;
      color: #f0f0f0;
      cursor: pointer;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .model-option:hover {
      background: rgba(33, 150, 243, 0.2);
    }

    .model-option.selected {
      background: rgba(33, 150, 243, 0.3);
    }

    .model-option .model-name {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .model-option .provider-badge {
      font-size: 0.75rem;
      color: #888;
      background: rgba(255, 255, 255, 0.1);
      padding: 2px 6px;
      border-radius: 3px;
    }

    .recent-icon {
      color: #ffc107;
      font-size: 0.8rem;
    }

    .no-results {
      padding: 16px;
      text-align: center;
      color: #888;
      font-style: italic;
    }

    .clear-btn {
      padding: 4px 8px;
      background: transparent;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 3px;
      color: #888;
      font-size: 0.75rem;
      cursor: pointer;
      margin-left: 8px;
    }

    .clear-btn:hover {
      background: rgba(255, 255, 255, 0.1);
      color: #f0f0f0;
    }
  `;

  constructor() {
    super();
    this.isOpen = false;
    this.searchTerm = '';
    this.recentModels = [];
    this.providers = {};
    this.selectedValue = '';
    this._boundClickOutside = this._handleClickOutside.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    this._loadRecentModels();
    document.addEventListener('click', this._boundClickOutside);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    document.removeEventListener('click', this._boundClickOutside);
  }

  _handleClickOutside(e) {
    if (this.isOpen && !this.contains(e.target)) {
      this.isOpen = false;
    }
  }

  _loadRecentModels() {
    try {
      const stored = localStorage.getItem(RECENT_MODELS_KEY);
      if (stored) {
        const all = JSON.parse(stored);
        // Filter to only models for this service
        this.recentModels = (all[this.serviceName] || []).slice(0, MAX_RECENT);
      }
    } catch (e) {
      console.warn('Failed to load recent models:', e);
      this.recentModels = [];
    }
  }

  _saveRecentModel(provider, model) {
    try {
      const stored = localStorage.getItem(RECENT_MODELS_KEY);
      const all = stored ? JSON.parse(stored) : {};
      const key = `${provider}__${model}`;
      
      // Get or create array for this service
      let serviceRecent = all[this.serviceName] || [];
      
      // Remove if already exists
      serviceRecent = serviceRecent.filter(m => m.key !== key);
      
      // Add to front
      serviceRecent.unshift({ key, provider, model });
      
      // Limit size
      serviceRecent = serviceRecent.slice(0, MAX_RECENT);
      
      all[this.serviceName] = serviceRecent;
      localStorage.setItem(RECENT_MODELS_KEY, JSON.stringify(all));
      
      this.recentModels = serviceRecent;
    } catch (e) {
      console.warn('Failed to save recent model:', e);
    }
  }

  _toggleDropdown(e) {
    e.stopPropagation();
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.searchTerm = '';
      // Focus search input after render
      this.updateComplete.then(() => {
        const input = this.shadowRoot.querySelector('.search-input');
        if (input) input.focus();
      });
    }
  }

  _handleSearch(e) {
    this.searchTerm = e.target.value;
  }

  _selectModel(provider, model) {
    const value = `${provider}__${model}`;
    this.selectedValue = value;
    this._saveRecentModel(provider, model);
    this.isOpen = false;
    
    // Dispatch change event
    this.dispatchEvent(new CustomEvent('model-change', {
      detail: { provider, model, value },
      bubbles: true,
      composed: true
    }));
  }

  _getSelectedDisplay() {
    if (!this.selectedValue) {
      return { provider: '', model: 'Select a model...' };
    }
    const [provider, model] = this.selectedValue.split('__');
    return { provider, model };
  }

  _getFilteredModels() {
    const term = this.searchTerm.toLowerCase();
    const results = [];
    
    if (!this.providers) return results;
    
    for (const [provider, models] of Object.entries(this.providers)) {
      const filteredModels = models.filter(model => 
        !term || 
        model.toLowerCase().includes(term) ||
        provider.toLowerCase().includes(term)
      );
      
      if (filteredModels.length > 0) {
        results.push({ provider, models: filteredModels });
      }
    }
    
    return results;
  }

  _getFilteredRecent() {
    const term = this.searchTerm.toLowerCase();
    return this.recentModels.filter(m => 
      !term ||
      m.model.toLowerCase().includes(term) ||
      m.provider.toLowerCase().includes(term)
    );
  }

  _render() {
    const selected = this._getSelectedDisplay();
    const filteredModels = this._getFilteredModels();
    const filteredRecent = this._getFilteredRecent();
    const hasResults = filteredModels.length > 0 || filteredRecent.length > 0;

    return html`
      <div class="selector-container">
        <div class="selected-display ${this.isOpen ? 'open' : ''}" 
             @click=${this._toggleDropdown}>
          ${selected.provider ? html`
            <span class="selected-provider">${selected.provider}</span>
          ` : ''}
          <span class="selected-text">${selected.model}</span>
          <span class="dropdown-arrow ${this.isOpen ? 'open' : ''}">▼</span>
        </div>
        
        ${this.isOpen ? html`
          <div class="dropdown">
            <div class="search-box">
              <input type="text" 
                     class="search-input" 
                     placeholder="Search models..."
                     .value=${this.searchTerm}
                     @input=${this._handleSearch}
                     @click=${(e) => e.stopPropagation()}>
            </div>
            
            ${!hasResults ? html`
              <div class="no-results">No models found</div>
            ` : ''}
            
            ${filteredRecent.length > 0 ? html`
              <div class="section-header">★ Recent</div>
              ${filteredRecent.map(m => html`
                <div class="model-option ${this.selectedValue === m.key ? 'selected' : ''}"
                     @click=${() => this._selectModel(m.provider, m.model)}>
                  <span class="recent-icon">★</span>
                  <span class="model-name">${m.model}</span>
                  <span class="provider-badge">${m.provider}</span>
                </div>
              `)}
            ` : ''}
            
            ${filteredModels.map(group => html`
              <div class="provider-header">${group.provider}</div>
              ${group.models.map(model => html`
                <div class="model-option ${this.selectedValue === `${group.provider}__${model}` ? 'selected' : ''}"
                     @click=${() => this._selectModel(group.provider, model)}>
                  <span class="model-name">${model}</span>
                </div>
              `)}
            `)}
          </div>
        ` : ''}
      </div>
    `;
  }
}

customElements.define('model-selector', ModelSelector);
