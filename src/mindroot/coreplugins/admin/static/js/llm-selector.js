import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

const RECENT_LLMS_KEY = 'mindroot-recent-llms';
const MAX_RECENT_LLMS = 6;

class LlmSelector extends BaseEl {
  static properties = {
    serviceModels: { type: Object, state: true },
    recentLlms: { type: Array, state: true },
    selectedLlm: { type: String, state: true },
    initialValue: { type: String, reflect: true },
    loading: { type: Boolean, state: true },
  };

  static styles = css`
    :host {
      display: block;
      margin-bottom: 1rem;
    }
    label {
      display: block;
      margin-bottom: 0.5rem;
      color: var(--gray-700, #4A5568);
      font-weight: 500;
    }
    select {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid var(--gray-300, #CBD5E0);
      border-radius: 0.375rem;
      background-color: var(--white, #FFFFFF);
      color: var(--gray-700, #4A5568);
      font-size: 0.9rem;
      box-sizing: border-box;
      transition: border-color 0.2s ease;
    }
    select:focus {
      outline: none;
      border-color: var(--primary-500, #667EEA);
      box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
    .loading-text {
      color: var(--gray-500);
      padding: 0.75rem 0;
    }
  `;

  constructor() {
    super();
    this.serviceModels = {}; 
    this.recentLlms = [];
    this.selectedLlm = '';
    this.initialValue = '';
    this.loading = true;
    this.fetchServiceModels();
    this.loadRecentLlms();
    // make a very obvious message in orange in the console saying LlmSelector is loaded
     console.log('%cLlmSelector is loaded', 'color: orange; font-size: 20px; font-weight: bold;');
  }

  attributeChangedCallback(name, oldValue, newValue) {
    super.attributeChangedCallback(name, oldValue, newValue);
    
    if (name === 'initial-value' && newValue && newValue !== oldValue) {
      console.log('Initial value attribute changed:', newValue);
      this.initialValue = newValue;
      this.selectedLlm = newValue;
      this.saveRecentLlm(newValue);
    }
  }

  async fetchServiceModels() {
    this.loading = true;
    try {
      const response = await fetch('/service-models');
      if (!response.ok) { 
        throw new Error(`Failed to fetch service models: ${response.statusText}`);
      }
      const data = await response.json();
      // Check if data has the expected structure
      if (data && data.llm && typeof data.llm === 'object') { 
        this.serviceModels = { llm: data.llm };
      } else {
        // Look for stream_chat models instead of llm
        if (data && data.stream_chat && typeof data.stream_chat === 'object') {
          this.serviceModels = { llm: data.stream_chat };
        } else {
          this.serviceModels = { llm: {} };
        }
      } 
    } catch (error) {
      console.error('Error fetching service models:', error);
      this.serviceModels = { llm: {} }; 
    } finally {
      this.loading = false;
    }
  }

  loadRecentLlms() {
    try {
      const stored = localStorage.getItem(RECENT_LLMS_KEY);
      if (stored) {
        const parsedLlms = JSON.parse(stored);
        if (Array.isArray(parsedLlms)) {
          this.recentLlms = parsedLlms;
        }
      }
    } catch (e) {
      console.error('Error loading recent LLMs from localStorage:', e); 
      this.recentLlms = []; 
    }
    
    // If an initial value was provided, use it
    if (this.initialValue && this.initialValue !== '') {
      this.selectedLlm = this.initialValue;
      this.saveRecentLlm(this.initialValue);
    }
  }

  saveRecentLlm(llmIdentifier) {
    if (!llmIdentifier || llmIdentifier === '') return;

    let updatedRecentLlms = [llmIdentifier, ...this.recentLlms.filter(item => item !== llmIdentifier)];
    if (updatedRecentLlms.length > MAX_RECENT_LLMS) {
      updatedRecentLlms = updatedRecentLlms.slice(0, MAX_RECENT_LLMS);
    }
    this.recentLlms = updatedRecentLlms;
    try {
      localStorage.setItem(RECENT_LLMS_KEY, JSON.stringify(this.recentLlms));
    } catch (e) {
      console.error('Error saving recent LLMs to localStorage:', e);
    }
  }

  handleLlmChange(event) {
    const newSelectedLlm = event.target.value;
    this.selectedLlm = newSelectedLlm;
    this.saveRecentLlm(newSelectedLlm);
    console.log('Selected LLM changed:', newSelectedLlm); 
    this.dispatch('llm-selected', { value: newSelectedLlm });
  }

  // Public method to update the selected LLM from outside
  updateSelectedLlm(llmIdentifier) {
    if (llmIdentifier && llmIdentifier !== this.selectedLlm) {
      this.selectedLlm = llmIdentifier;
      this.saveRecentLlm(llmIdentifier);
    }
  }

  _render() {
    if (this.loading) {
      return html`<div class=\"loading-text\">Loading LLM models...</div>`;
    }

    const llmProviders = this.serviceModels.llm || {};

    return html`
      <label for="llm-select">Select LLM Model</label>
      <select id="llm-select" @change=${e => this.handleLlmChange(e)} .value=${this.selectedLlm}>
        <option value="">-- Select an LLM --</option>
        
        ${this.recentLlms.length > 0 ? html`
          <optgroup label="Recently Used">
            ${this.recentLlms.map(llmIdentifier => {
              const parts = llmIdentifier.split('__');
              const provider = parts.length > 1 ? parts[0] : '';
              const modelName = parts.length > 1 ? parts[1] : llmIdentifier; 
              return html`<option value="${llmIdentifier}" ?selected=${llmIdentifier === this.selectedLlm}>${provider ? provider + ': ' : ''}${modelName}</option>`;
            })}
          </optgroup>
        ` : html``}

        ${Object.entries(llmProviders).map(([provider, models]) => {
          if (!Array.isArray(models)) return ''; 
          return html`
            <optgroup label="${provider}">
              ${models.map(modelName => {
                const llmIdentifier = `${provider}__${modelName}`;
                return html`
                  <option value="${llmIdentifier}" ?selected=${llmIdentifier === this.selectedLlm}>${modelName}</option>
                `;
              })}
            </optgroup>
          `;
        })}
      </select>
    `;
  }
}

customElements.define('llm-selector', LlmSelector);
