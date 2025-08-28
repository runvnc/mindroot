import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class ModelPreferencesV2 extends BaseEl {
  static properties = {
    preferences: { type: Object },
    serviceModels: { type: Object },
    loading: { type: Boolean },
    saving: { type: Boolean },
    selectedService: { type: String },
    availableServices: { type: Array }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .preferences-v2-container {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      gap: 20px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section h3 {
      margin: 0 0 1rem 0;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .service-selector {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-bottom: 1rem;
    }

    .service-selector select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      min-width: 150px;
    }

    .provider-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .provider-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 0.75rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .provider-item.dragging {
      opacity: 0.5;
    }

    .drag-handle {
      cursor: grab;
      color: #888;
      font-size: 1.2em;
    }

    .drag-handle:active {
      cursor: grabbing;
    }

    .provider-info {
      flex: 1;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .provider-name {
      font-weight: 500;
      color: #fff;
      min-width: 120px;
    }

    .model-select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      min-width: 200px;
    }

    .order-controls {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .order-btn {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.25rem 0.5rem;
      border-radius: 2px;
      cursor: pointer;
      font-size: 0.8em;
    }

    .order-btn:hover {
      background: #3a3a50;
    }

    .order-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .remove-btn {
      background: #402a2a;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
      cursor: pointer;
    }

    .remove-btn:hover {
      background: #503a3a;
    }

    .add-provider {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 1rem;
      padding: 1rem;
      background: rgba(0, 0, 0, 0.1);
      border-radius: 4px;
      border: 1px dashed rgba(255, 255, 255, 0.2);
    }

    .add-provider select {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem;
      border-radius: 4px;
    }

    .add-btn {
      background: #2a402a;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
    }

    .add-btn:hover {
      background: #3a503a;
    }

    .actions {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }

    .save-btn {
      background: #2a402a;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.75rem 1.5rem;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 500;
    }

    .save-btn:hover {
      background: #3a503a;
    }

    .save-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .migrate-btn {
      background: #403a2a;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.75rem 1.5rem;
      border-radius: 4px;
      cursor: pointer;
    }

    .migrate-btn:hover {
      background: #504a3a;
    }

    .loading {
      text-align: center;
      color: #888;
      padding: 2rem;
    }

    .error {
      color: #ff6b6b;
      background: rgba(255, 107, 107, 0.1);
      padding: 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;
    }

    .success {
      color: #51cf66;
      background: rgba(81, 207, 102, 0.1);
      padding: 1rem;
      border-radius: 4px;
      margin-bottom: 1rem;
    }
  `;

  constructor() {
    super();
    this.preferences = {};
    this.serviceModels = {};
    this.loading = true;
    this.saving = false;
    this.selectedService = '';
    this.availableServices = [];
    this.fetchData();
  }

  async fetchData() {
    this.loading = true;
    try {
      await Promise.all([
        this.fetchPreferences(),
        this.fetchServiceModels()
      ]);
      this.updateAvailableServices();
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      this.loading = false;
    }
  }

  async fetchPreferences() {
    try {
      const response = await fetch('/settings_v2');
      if (response.ok) {
        this.preferences = await response.json();
      } else {
        console.log('V2 preferences not available, using empty preferences');
        this.preferences = {};
      }
    } catch (error) {
      console.error('Error fetching v2 preferences:', error);
      this.preferences = {};
    }
  }

  async fetchServiceModels() {
    try {
      const response = await fetch('/service-models');
      this.serviceModels = await response.json();
    } catch (error) {
      console.error('Error fetching service models:', error);
      this.serviceModels = {};
    }
  }

  updateAvailableServices() {
    const services = new Set();
    
    // Add services from current preferences
    Object.keys(this.preferences).forEach(service => services.add(service));
    
    // Add services from available service models
    Object.keys(this.serviceModels).forEach(service => services.add(service));
    
    this.availableServices = Array.from(services).sort();
    
    if (!this.selectedService && this.availableServices.length > 0) {
      this.selectedService = this.availableServices[0];
    }
  }

  handleServiceChange(event) {
    this.selectedService = event.target.value;
  }

  moveProviderUp(index) {
    if (index === 0) return;
    
    const servicePrefs = [...(this.preferences[this.selectedService] || [])];
    [servicePrefs[index - 1], servicePrefs[index]] = [servicePrefs[index], servicePrefs[index - 1]];
    
    this.preferences = {
      ...this.preferences,
      [this.selectedService]: servicePrefs
    };
  }

  moveProviderDown(index) {
    const servicePrefs = this.preferences[this.selectedService] || [];
    if (index === servicePrefs.length - 1) return;
    
    const newPrefs = [...servicePrefs];
    [newPrefs[index], newPrefs[index + 1]] = [newPrefs[index + 1], newPrefs[index]];
    
    this.preferences = {
      ...this.preferences,
      [this.selectedService]: newPrefs
    };
  }

  removeProvider(index) {
    const servicePrefs = [...(this.preferences[this.selectedService] || [])];
    servicePrefs.splice(index, 1);
    
    this.preferences = {
      ...this.preferences,
      [this.selectedService]: servicePrefs
    };
  }

  updateProviderModel(index, newModel) {
    const servicePrefs = [...(this.preferences[this.selectedService] || [])];
    if (servicePrefs[index]) {
      servicePrefs[index] = [servicePrefs[index][0], newModel];
      
      this.preferences = {
        ...this.preferences,
        [this.selectedService]: servicePrefs
      };
    }
  }

  addProvider() {
    const providerSelect = this.shadowRoot.querySelector('.add-provider-select');
    const modelSelect = this.shadowRoot.querySelector('.add-model-select');
    
    const provider = providerSelect.value;
    const model = modelSelect.value;
    
    if (!provider || !model) return;
    
    const servicePrefs = [...(this.preferences[this.selectedService] || [])];
    
    // Check if this provider/model combination already exists
    const exists = servicePrefs.some(([p, m]) => p === provider && m === model);
    if (exists) return;
    
    servicePrefs.push([provider, model]);
    
    this.preferences = {
      ...this.preferences,
      [this.selectedService]: servicePrefs
    };
    
    // Reset selects
    providerSelect.value = '';
    modelSelect.value = '';
  }

  async savePreferences() {
    this.saving = true;
    try {
      const response = await fetch('/settings_v2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(this.preferences)
      });
      
      if (response.ok) {
        this.showMessage('Preferences saved successfully!', 'success');
      } else {
        const error = await response.text();
        this.showMessage(`Error saving preferences: ${error}`, 'error');
      }
    } catch (error) {
      this.showMessage(`Error saving preferences: ${error.message}`, 'error');
    } finally {
      this.saving = false;
    }
  }

  async migrateFromOld() {
    try {
      const response = await fetch('/migrate_settings', {
        method: 'POST'
      });
      
      if (response.ok) {
        const result = await response.json();
        this.showMessage(result.message, 'success');
        await this.fetchPreferences();
      } else {
        const error = await response.text();
        this.showMessage(`Migration failed: ${error}`, 'error');
      }
    } catch (error) {
      this.showMessage(`Migration failed: ${error.message}`, 'error');
    }
  }

  showMessage(message, type) {
    // Simple message display - could be enhanced with a proper notification system
    const messageEl = document.createElement('div');
    messageEl.className = type;
    messageEl.textContent = message;
    
    const container = this.shadowRoot.querySelector('.preferences-v2-container');
    container.insertBefore(messageEl, container.firstChild);
    
    setTimeout(() => {
      messageEl.remove();
    }, 5000);
  }

  getAvailableProviders() {
    if (!this.selectedService || !this.serviceModels[this.selectedService]) {
      return [];
    }
    return Object.keys(this.serviceModels[this.selectedService]);
  }

  getAvailableModels(provider) {
    if (!this.selectedService || !this.serviceModels[this.selectedService] || !provider) {
      return [];
    }
    return this.serviceModels[this.selectedService][provider] || [];
  }

  _render() {
    if (this.loading) {
      return html`<div class="loading">Loading preferences...</div>`;
    }

    const currentServicePrefs = this.preferences[this.selectedService] || [];
    const availableProviders = this.getAvailableProviders();

    return html`
      <div class="preferences-v2-container">
        <div class="section">
          <h3>
            <span class="material-icons">tune</span>
            Model Preferences
          </h3>
          
          <div class="service-selector">
            <label>Service:</label>
            <select @change=${this.handleServiceChange} .value=${this.selectedService}>
              ${this.availableServices.map(service => html`
                <option value="${service}">${service}</option>
              `)}
            </select>
          </div>

          ${this.selectedService ? html`
            <div class="provider-list">
              ${currentServicePrefs.map((providerModel, index) => {
                const [provider, model] = providerModel;
                const availableModels = this.getAvailableModels(provider);
                
                return html`
                  <div class="provider-item">
                    <span class="drag-handle material-icons">drag_indicator</span>
                    
                    <div class="provider-info">
                      <span class="provider-name">${provider}</span>
                      <select 
                        class="model-select" 
                        .value=${model}
                        @change=${(e) => this.updateProviderModel(index, e.target.value)}
                      >
                        ${availableModels.map(availableModel => html`
                          <option value="${availableModel}" ?selected=${availableModel === model}>
                            ${availableModel}
                          </option>
                        `)}
                      </select>
                    </div>
                    
                    <div class="order-controls">
                      <button 
                        class="order-btn" 
                        ?disabled=${index === 0}
                        @click=${() => this.moveProviderUp(index)}
                      >↑</button>
                      <button 
                        class="order-btn" 
                        ?disabled=${index === currentServicePrefs.length - 1}
                        @click=${() => this.moveProviderDown(index)}
                      >↓</button>
                    </div>
                    
                    <button class="remove-btn" @click=${() => this.removeProvider(index)}>
                      <span class="material-icons">delete</span>
                    </button>
                  </div>
                `;
              })}
            </div>

            <div class="add-provider">
              <label>Add Provider:</label>
              <select class="add-provider-select">
                <option value="">Select Provider</option>
                ${availableProviders.map(provider => html`
                  <option value="${provider}">${provider}</option>
                `)}
              </select>
              
              <label>Model:</label>
              <select class="add-model-select">
                <option value="">Select Model</option>
              </select>
              
              <button class="add-btn" @click=${this.addProvider}>Add</button>
            </div>
          ` : html`<p>Select a service to configure preferences.</p>`}
        </div>

        <div class="actions">
          <button class="migrate-btn" @click=${this.migrateFromOld}>
            Migrate from Old Format
          </button>
          <button 
            class="save-btn" 
            ?disabled=${this.saving}
            @click=${this.savePreferences}
          >
            ${this.saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    `;
  }

  updated(changedProperties) {
    super.updated(changedProperties);
    
    // Update model dropdown when provider changes
    if (changedProperties.has('selectedService')) {
      const providerSelect = this.shadowRoot.querySelector('.add-provider-select');
      const modelSelect = this.shadowRoot.querySelector('.add-model-select');
      
      if (providerSelect && modelSelect) {
        providerSelect.addEventListener('change', (e) => {
          const selectedProvider = e.target.value;
          const availableModels = this.getAvailableModels(selectedProvider);
          
          modelSelect.innerHTML = '<option value="">Select Model</option>' +
            availableModels.map(model => `<option value="${model}">${model}</option>`).join('');
        });
      }
    }
  }
}

customElements.define('model-preferences-v2', ModelPreferencesV2);
