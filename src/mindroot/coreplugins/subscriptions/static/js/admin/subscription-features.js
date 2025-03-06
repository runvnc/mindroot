import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class SubscriptionFeatures extends BaseEl {
  static properties = {
    features: { type: Array },
    loading: { type: Boolean },
    showNewFeatureForm: { type: Boolean },
    editingFeature: { type: Object }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .header-actions {
      display: flex;
      justify-content: flex-end;
      margin-bottom: 1rem;
    }

    .features-list {
      margin-bottom: 2rem;
    }
    
    .feature-card {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .feature-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }
    
    .feature-name {
      font-size: 1.1rem;
      font-weight: 500;
    }
    
    .feature-type {
      font-size: 0.9rem;
      padding: 0.25rem 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
    }
    
    .feature-description {
      margin-bottom: 0.5rem;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .feature-options {
      margin-top: 0.5rem;
      padding-top: 0.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .feature-option {
      display: inline-block;
      margin-right: 0.5rem;
      margin-bottom: 0.5rem;
      padding: 0.25rem 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      font-size: 0.9rem;
    }

    .new-feature-form {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 1rem;
    }
    
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }
    
    .form-group {
      margin-bottom: 1rem;
    }
    
    .form-label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }
    
    .form-control {
      width: 100%;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: white;
    }
    
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
    }
    
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      font-weight: 500;
    }
    
    .btn-primary {
      background: #4a5af8;
      color: white;
    }
    
    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }
    
    .btn-danger {
      background: #f85a5a;
      color: white;
    }
    
    .btn-sm {
      padding: 0.25rem 0.5rem;
      font-size: 0.8rem;
    }
  `;

  constructor() {
    super();
    this.features = [];
    this.loading = false;
    this.showNewFeatureForm = false;
    this.editingFeature = null;
  }

  toggleNewFeatureForm() {
    this.showNewFeatureForm = !this.showNewFeatureForm;
    this.editingFeature = null;
  }

  editFeature(feature) {
    this.editingFeature = {...feature};
    this.showNewFeatureForm = true;
  }

  toggleOptionsField() {
    const featureType = this.shadowRoot.querySelector('#feature_type').value;
    const optionsContainer = this.shadowRoot.querySelector('#options_container');
    
    if (featureType === 'select') {
      optionsContainer.style.display = 'block';
    } else {
      optionsContainer.style.display = 'none';
    }
  }

  async handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const featureData = {};
    
    for (const [key, value] of formData.entries()) {
      if (key === 'display_order') {
        featureData[key] = parseInt(value);
      } else if (key === 'options') {
        // Convert options text to array
        featureData[key] = value.split('\n').filter(opt => opt.trim() !== '');
      } else {
        featureData[key] = value;
      }
    }
    
    // Set default value based on type
    if (featureData.type === 'boolean') {
      featureData.default_value = featureData.default_value === 'true';
    } else if (featureData.type === 'number') {
      featureData.default_value = parseFloat(featureData.default_value) || 0;
    }
    
    try {
      let response;
      let result;
      
      if (this.editingFeature) {
        // Update existing feature
        response = await fetch(`/admin/subscriptions/features/${this.editingFeature.feature_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(featureData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Feature updated successfully!');
          this.dispatchEvent(new CustomEvent('feature-updated', {
            detail: result.feature,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to update feature: ' + (result.message || 'Unknown error'));
        }
      } else {
        // Create new feature
        response = await fetch('/admin/subscriptions/features', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(featureData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Feature created successfully!');
          this.dispatchEvent(new CustomEvent('feature-created', {
            detail: result.feature,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to create feature: ' + (result.message || 'Unknown error'));
        }
      }
      
      // Reset form and state
      this.showNewFeatureForm = false;
      this.editingFeature = null;
      form.reset();
      
    } catch (error) {
      alert('Error saving feature: ' + error.message);
    }
  }

  async activateFeature(featureId) {
    try {
      const response = await fetch(`/admin/subscriptions/features/${featureId}/activate`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert('Feature activated successfully!');
        this.dispatchEvent(new CustomEvent('feature-updated', {
          bubbles: true,
          composed: true
        }));
      } else {
        alert('Failed to activate feature: ' + (result.message || 'Unknown error'));
      }
    } catch (error) {
      alert('Error activating feature: ' + error.message);
    }
  }

  async deactivateFeature(featureId) {
    if (confirm('Are you sure you want to deactivate this feature?')) {
      try {
        const response = await fetch(`/admin/subscriptions/features/${featureId}/deactivate`, {
          method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
          alert('Feature deactivated successfully!');
          this.dispatchEvent(new CustomEvent('feature-updated', {
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to deactivate feature: ' + (result.message || 'Unknown error'));
        }
      } catch (error) {
        alert('Error deactivating feature: ' + error.message);
      }
    }
  }

  updated(changedProperties) {
    super.updated(changedProperties);
    if (this.showNewFeatureForm) {
      // Initialize options container visibility
      setTimeout(() => {
        const featureType = this.shadowRoot.querySelector('#feature_type');
        if (featureType) {
          this.toggleOptionsField();
          featureType.addEventListener('change', () => this.toggleOptionsField());
        }
      }, 0);
    }
  }

  render() {
    return html`
      <div>
        <div class="header-actions">
          <button class="btn btn-primary" @click=${this.toggleNewFeatureForm}>
            ${this.showNewFeatureForm ? 'Cancel' : 'New Feature'}
          </button>
        </div>

        ${this.showNewFeatureForm ? html`
          <div class="new-feature-form">
            <h3>${this.editingFeature ? 'Edit Feature' : 'Create New Feature'}</h3>
            <form @submit=${this.handleSubmit}>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label" for="feature_name">Feature Name</label>
                  <input type="text" class="form-control" id="feature_name" name="name" 
                         value=${this.editingFeature?.name || ''} required>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="feature_type">Type</label>
                  <select class="form-control" id="feature_type" name="type">
                    <option value="boolean" ?selected=${this.editingFeature?.type === 'boolean'}>Boolean (Yes/No)</option>
                    <option value="number" ?selected=${this.editingFeature?.type === 'number'}>Number</option>
                    <option value="text" ?selected=${this.editingFeature?.type === 'text'}>Text</option>
                    <option value="select" ?selected=${this.editingFeature?.type === 'select'}>Select (Options)</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="display_order">Display Order</label>
                  <input type="number" class="form-control" id="display_order" name="display_order" 
                         value=${this.editingFeature?.display_order || '0'}>
                </div>
                
                <div class="form-group" id="default_value_container">
                  <label class="form-label" for="default_value">Default Value</label>
                  <input type="text" class="form-control" id="default_value" name="default_value" 
                         value=${this.editingFeature?.default_value || ''}>
                </div>
              </div>
              
              <div class="form-group" id="options_container" style="display: none;">
                <label class="form-label" for="options">Options (one per line)</label>
                <textarea class="form-control" id="options" name="options" rows="3">
                  ${this.editingFeature?.options ? this.editingFeature.options.join('\n') : ''}
                </textarea>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="feature_description">Description</label>
                <textarea class="form-control" id="feature_description" name="description" rows="2" required>
                  ${this.editingFeature?.description || ''}
                </textarea>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn btn-secondary" @click=${this.toggleNewFeatureForm}>
                  Cancel
                </button>
                
                <button type="submit" class="btn btn-primary">
                  ${this.editingFeature ? 'Update Feature' : 'Create Feature'}
                </button>
              </div>
            </form>
          </div>
        ` : ''}

        <div class="features-list">
          ${this.loading ? html`<p>Loading features...</p>` : ''}
          
          ${!this.loading && this.features.length === 0 ? html`<p>No features defined yet.</p>` : ''}
          
          ${this.features.map(feature => {
            let optionsHtml = '';
            
            if (feature.type === 'select' && feature.options && feature.options.length > 0) {
              optionsHtml = html`
                <div class="feature-options">
                  ${feature.options.map(option => html`
                    <span class="feature-option">${option}</span>
                  `)}
                </div>
              `;
            }
            
            return html`
              <div class="feature-card">
                <div class="feature-header">
                  <div class="feature-name">${feature.name}</div>
                  <div class="feature-type">${feature.type}</div>
                </div>
                
                <div class="feature-description">${feature.description}</div>
                
                <div>
                  <strong>Default:</strong> 
                  ${feature.type === 'boolean' ? 
                    (feature.default_value ? 'Yes' : 'No') : 
                    (feature.default_value !== null ? feature.default_value : 'None')}
                </div>
                
                ${optionsHtml}
                
                <div class="plan-actions" style="margin-top: 0.5rem;">
                  <button class="btn btn-secondary btn-sm" @click=${() => this.editFeature(feature)}>
                    Edit
                  </button>
                  
                  ${feature.active ? html`
                    <button class="btn btn-danger btn-sm" @click=${() => this.deactivateFeature(feature.feature_id)}>
                      Deactivate
                    </button>
                  ` : html`
                    <button class="btn btn-primary btn-sm" @click=${() => this.activateFeature(feature.feature_id)}>
                      Activate
                    </button>
                  `}
                </div>
              </div>
            `;
          })}
        </div>
      </div>
    `;
  }
}

customElements.define('subscription-features', SubscriptionFeatures);
