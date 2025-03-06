import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class SubscriptionPlans extends BaseEl {
  static properties = {
    plans: { type: Array },
    features: { type: Array },
    loading: { type: Boolean },
    showNewPlanForm: { type: Boolean },
    editingPlan: { type: Object },
    selectedFeatures: { type: Object }
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

    .subscription-plans {
      margin-bottom: 2rem;
    }
    
    .plan-card {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .plan-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
    }
    
    .plan-title {
      font-size: 1.2rem;
      font-weight: 500;
    }
    
    .plan-price {
      font-size: 1.1rem;
    }
    
    .plan-description {
      margin-bottom: 1rem;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .plan-details {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }
    
    .plan-detail {
      background: rgba(0, 0, 0, 0.2);
      padding: 0.5rem;
      border-radius: 4px;
    }
    
    .plan-detail-label {
      font-size: 0.8rem;
      color: rgba(255, 255, 255, 0.5);
      margin-bottom: 0.25rem;
    }
    
    .plan-detail-value {
      font-weight: 500;
    }
    
    .plan-actions {
      display: flex;
      gap: 0.5rem;
    }
    
    .new-plan-form {
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

    .features-section {
      margin-top: 1.5rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      padding-top: 1rem;
    }

    .features-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 0.75rem;
      margin-top: 0.75rem;
    }

    .feature-item {
      display: flex;
      align-items: center;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.5rem;
      border-radius: 4px;
    }

    .feature-checkbox {
      margin-right: 0.5rem;
    }

    .feature-value-container {
      display: flex;
      align-items: center;
      margin-top: 0.5rem;
    }

    .feature-value-input {
      width: 100%;
      max-width: 150px;
      margin-left: 0.5rem;
    }

    .feature-tag {
      display: inline-block;
      background: rgba(74, 90, 248, 0.2);
      border: 1px solid rgba(74, 90, 248, 0.5);
      border-radius: 4px;
      padding: 0.25rem 0.5rem;
      margin-right: 0.5rem;
      margin-bottom: 0.5rem;
      font-size: 0.9rem;
    }

    .plan-features {
      margin-top: 1rem;
      display: flex;
      flex-wrap: wrap;
    }
  `;

  constructor() {
    super();
    this.plans = [];
    this.features = [];
    this.loading = false;
    this.showNewPlanForm = false;
    this.editingPlan = null;
    this.selectedFeatures = {};
  }

  toggleNewPlanForm() {
    this.showNewPlanForm = !this.showNewPlanForm;
    if (!this.showNewPlanForm) {
      this.editingPlan = null;
      this.selectedFeatures = {};
    }
  }

  editPlan(plan) {
    this.editingPlan = {...plan};
    this.selectedFeatures = {...(plan.features || {})};
    this.showNewPlanForm = true;
  }

  handleFeatureChange(e, feature) {
    const checked = e.target.checked;
    const featureId = feature.feature_id;
    
    if (checked) {
      // Initialize with default value based on feature type
      let defaultValue;
      switch (feature.type) {
        case 'boolean':
          defaultValue = true;
          break;
        case 'number':
          defaultValue = feature.default_value || 0;
          break;
        case 'select':
          defaultValue = feature.options && feature.options.length > 0 ? 
                        feature.options[0] : '';
          break;
        default:
          defaultValue = feature.default_value || '';
      }
      
      this.selectedFeatures = {
        ...this.selectedFeatures,
        [feature.name]: defaultValue
      };
    } else {
      // Remove feature
      const newFeatures = {...this.selectedFeatures};
      delete newFeatures[feature.name];
      this.selectedFeatures = newFeatures;
    }
    
    this.requestUpdate();
  }

  handleFeatureValueChange(e, featureName) {
    const value = e.target.value;
    const type = e.target.type;
    
    let processedValue;
    if (type === 'checkbox') {
      processedValue = e.target.checked;
    } else if (type === 'number') {
      processedValue = parseFloat(value);
    } else {
      processedValue = value;
    }
    
    this.selectedFeatures = {
      ...this.selectedFeatures,
      [featureName]: processedValue
    };
  }

  isFeatureSelected(featureName) {
    return featureName in this.selectedFeatures;
  }

  getFeatureValue(featureName, defaultValue = '') {
    return this.selectedFeatures[featureName] !== undefined ? 
           this.selectedFeatures[featureName] : defaultValue;
  }

  async handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const planData = {};
    
    for (const [key, value] of formData.entries()) {
      // Convert numeric values
      if (key === 'price' || key === 'credits_per_cycle') {
        planData[key] = parseFloat(value);
      } else {
        planData[key] = value;
      }
    }
    
    // Add features
    planData.features = this.selectedFeatures;
    
    try {
      let response;
      let result;
      
      if (this.editingPlan) {
        // Update existing plan
        response = await fetch(`/admin/subscriptions/plans/${this.editingPlan.plan_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(planData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Plan updated successfully!');
          this.dispatchEvent(new CustomEvent('plan-updated', {
            detail: result.plan,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to update plan: ' + (result.message || 'Unknown error'));
        }
      } else {
        // Create new plan
        response = await fetch('/admin/subscriptions/plans', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(planData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Plan created successfully!');
          this.dispatchEvent(new CustomEvent('plan-created', {
            detail: result.plan,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to create plan: ' + (result.message || 'Unknown error'));
        }
      }
      
      // Reset form and state
      this.showNewPlanForm = false;
      this.editingPlan = null;
      this.selectedFeatures = {};
      form.reset();
      
    } catch (error) {
      alert('Error saving plan: ' + error.message);
    }
  }

  async activatePlan(planId) {
    try {
      const response = await fetch(`/admin/subscriptions/plans/${planId}/activate`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert('Plan activated successfully!');
        this.dispatchEvent(new CustomEvent('plan-updated', {
          bubbles: true,
          composed: true
        }));
      } else {
        alert('Failed to activate plan: ' + (result.message || 'Unknown error'));
      }
    } catch (error) {
      alert('Error activating plan: ' + error.message);
    }
  }

  async deactivatePlan(planId) {
    if (confirm('Are you sure you want to deactivate this plan?')) {
      try {
        const response = await fetch(`/admin/subscriptions/plans/${planId}`, {
          method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
          alert('Plan deactivated successfully!');
          this.dispatchEvent(new CustomEvent('plan-updated', {
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to deactivate plan: ' + (result.message || 'Unknown error'));
        }
      } catch (error) {
        alert('Error deactivating plan: ' + error.message);
      }
    }
  }

  renderFeatureValueInput(feature) {
    const featureName = feature.name;
    const isSelected = this.isFeatureSelected(featureName);
    
    if (!isSelected) return html``;
    
    switch (feature.type) {
      case 'boolean':
        return html`
          <div class="feature-value-container">
            <label>Value:</label>
            <input type="checkbox" 
                   class="feature-value-input" 
                   ?checked=${this.getFeatureValue(featureName, true)}
                   @change=${(e) => this.handleFeatureValueChange(e, featureName)}>
          </div>
        `;
      
      case 'number':
        return html`
          <div class="feature-value-container">
            <label>Value:</label>
            <input type="number" 
                   class="form-control feature-value-input" 
                   value=${this.getFeatureValue(featureName, feature.default_value || 0)}
                   @input=${(e) => this.handleFeatureValueChange(e, featureName)}>
          </div>
        `;
      
      case 'select':
        return html`
          <div class="feature-value-container">
            <label>Value:</label>
            <select class="form-control feature-value-input"
                    @change=${(e) => this.handleFeatureValueChange(e, featureName)}>
              ${feature.options.map(option => html`
                <option value=${option} 
                        ?selected=${this.getFeatureValue(featureName) === option}>
                  ${option}
                </option>
              `)}
            </select>
          </div>
        `;
      
      default: // text
        return html`
          <div class="feature-value-container">
            <label>Value:</label>
            <input type="text" 
                   class="form-control feature-value-input" 
                   value=${this.getFeatureValue(featureName, feature.default_value || '')}
                   @input=${(e) => this.handleFeatureValueChange(e, featureName)}>
          </div>
        `;
    }
  }

  renderFeatureTags(features) {
    if (!features || Object.keys(features).length === 0) {
      return html`<div>No features</div>`;
    }
    
    return html`
      <div class="plan-features">
        ${Object.entries(features).map(([name, value]) => html`
          <div class="feature-tag">
            ${name}: ${typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value}
          </div>
        `)}
      </div>
    `;
  }

  render() {
    return html`
      <div>
        <div class="header-actions">
          <button class="btn btn-primary" @click=${this.toggleNewPlanForm}>
            ${this.showNewPlanForm ? 'Cancel' : 'New Plan'}
          </button>
        </div>

        ${this.showNewPlanForm ? html`
          <div class="new-plan-form">
            <h3>${this.editingPlan ? 'Edit Plan' : 'Create New Plan'}</h3>
            <form @submit=${this.handleSubmit}>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label" for="name">Plan Name</label>
                  <input type="text" class="form-control" id="name" name="name" 
                         value=${this.editingPlan?.name || ''} required>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="price">Price</label>
                  <input type="number" class="form-control" id="price" name="price" step="0.01" 
                         value=${this.editingPlan?.price || ''} required>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="currency">Currency</label>
                  <select class="form-control" id="currency" name="currency">
                    ${['USD', 'EUR', 'GBP', 'CAD', 'AUD'].map(curr => html`
                      <option value=${curr} ?selected=${this.editingPlan?.currency === curr}>${curr}</option>
                    `)}
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="interval">Billing Interval</label>
                  <select class="form-control" id="interval" name="interval">
                    <option value="month" ?selected=${this.editingPlan?.interval === 'month'}>Monthly</option>
                    <option value="year" ?selected=${this.editingPlan?.interval === 'year'}>Yearly</option>
                  </select>
                </div>
                
                <div class="form-group">
                  <label class="form-label" for="credits_per_cycle">Credits Per Cycle</label>
                  <input type="number" class="form-control" id="credits_per_cycle" name="credits_per_cycle" 
                         value=${this.editingPlan?.credits_per_cycle || ''} required>
                </div>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="description">Description</label>
                <textarea class="form-control" id="description" name="description" rows="3" required>
                  ${this.editingPlan?.description || ''}
                </textarea>
              </div>
              
              <div class="features-section">
                <h4>Plan Features</h4>
                <p>Select features to include in this plan:</p>
                
                <div class="features-grid">
                  ${this.features.map(feature => html`
                    <div class="feature-item">
                      <input type="checkbox" 
                             class="feature-checkbox" 
                             id="feature-${feature.feature_id}" 
                             ?checked=${this.isFeatureSelected(feature.name)}
                             @change=${(e) => this.handleFeatureChange(e, feature)}>
                      <label for="feature-${feature.feature_id}">${feature.name}</label>
                      ${this.renderFeatureValueInput(feature)}
                    </div>
                  `)}
                </div>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn btn-secondary" @click=${this.toggleNewPlanForm}>
                  Cancel
                </button>
                
                <button type="submit" class="btn btn-primary">
                  ${this.editingPlan ? 'Update Plan' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        ` : ''}

        <div class="subscription-plans">
          ${this.loading ? html`<p>Loading plans...</p>` : ''}
          
          ${!this.loading && this.plans.length === 0 ? html`<p>No subscription plans found.</p>` : ''}
          
          ${this.plans.map(plan => html`
            <div class="plan-card">
              <div class="plan-header">
                <div class="plan-title">${plan.name}</div>
                <div class="plan-price">${plan.price} ${plan.currency}/${plan.interval}</div>
              </div>
              
              <div class="plan-description">${plan.description}</div>
              
              <div class="plan-details">
                <div class="plan-detail">
                  <div class="plan-detail-label">Credits Per Cycle</div>
                  <div class="plan-detail-value">${plan.credits_per_cycle}</div>
                </div>
                
                <div class="plan-detail">
                  <div class="plan-detail-label">Status</div>
                  <div class="plan-detail-value">${plan.active ? 'Active' : 'Inactive'}</div>
                </div>
                
                <div class="plan-detail">
                  <div class="plan-detail-label">Plan ID</div>
                  <div class="plan-detail-value">${plan.plan_id}</div>
                </div>
              </div>
              
              <div class="plan-detail">
                <div class="plan-detail-label">Features</div>
                ${this.renderFeatureTags(plan.features)}
              </div>
              
              <div class="plan-actions">
                <button class="btn btn-secondary btn-sm" @click=${() => this.editPlan(plan)}>
                  Edit
                </button>
                
                ${plan.active ? html`
                  <button class="btn btn-danger btn-sm" @click=${() => this.deactivatePlan(plan.plan_id)}>
                    Deactivate
                  </button>
                ` : html`
                  <button class="btn btn-primary btn-sm" @click=${() => this.activatePlan(plan.plan_id)}>
                    Activate
                  </button>
                `}
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}

customElements.define('subscription-plans', SubscriptionPlans);
