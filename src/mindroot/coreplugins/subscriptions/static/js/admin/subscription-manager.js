import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';
import './subscription-plans.js';
import './subscription-features.js';
import './subscription-templates.js';

class SubscriptionManager extends BaseEl {
  static properties = {
    plans: { type: Array },
    features: { type: Array },
    templates: { type: Array },
    selectedPlan: { type: Object },
    activeTab: { type: String },
    loading: { type: Boolean }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
      height: 100%;
    }

    .subscription-manager {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1600px;
      margin: 0 auto;
    }

    .admin-tabs {
      display: flex;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 1rem;
    }
    
    .admin-tab {
      padding: 0.75rem 1.5rem;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      margin-right: 1rem;
      font-weight: 500;
    }
    
    .admin-tab.active {
      border-bottom-color: #4a5af8;
      color: #4a5af8;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      display: flex;
      flex-direction: column;
      gap: 20px;
      height: 100%;
      min-height: 0;
    }

    .tab-content {
      display: none;
    }
    
    .tab-content.active {
      display: block;
    }
  `;

  constructor() {
    super();
    this.plans = [];
    this.features = [];
    this.templates = [];
    this.selectedPlan = null;
    this.activeTab = 'plans';
    this.loading = false;
    this.fetchInitialData();
  }

  async fetchInitialData() {
    this.loading = true;
    await Promise.all([
      this.fetchPlans(),
      this.fetchFeatures(),
      this.fetchTemplates()
    ]);
    this.loading = false;
  }

  async fetchPlans() {
    try {
      const response = await fetch('/admin/subscriptions/plans?active_only=false');
      const result = await response.json();
      if (result.status === 'success') {
        this.plans = result.plans;
      }
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
    }
  }

  async fetchFeatures() {
    try {
      const response = await fetch('/admin/subscriptions/features/list?active_only=false');
      const result = await response.json();
      if (result.status === 'success') {
        this.features = result.features;
      }
    } catch (error) {
      console.error('Error fetching features:', error);
    }
  }

  async fetchTemplates() {
    try {
      const response = await fetch('/admin/subscriptions/templates/list');
      const result = await response.json();
      if (result.status === 'success') {
        this.templates = result.templates;
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  }

  setActiveTab(tab) {
    this.activeTab = tab;
  }

  handlePlanCreated() {
    this.fetchPlans();
  }

  handlePlanUpdated() {
    this.fetchPlans();
  }

  handleFeatureCreated() {
    this.fetchFeatures();
  }

  handleFeatureUpdated() {
    this.fetchFeatures();
  }

  handleTemplateCreated() {
    this.fetchTemplates();
  }

  handleTemplateUpdated() {
    this.fetchTemplates();
  }

  render() {
    return html`
      <div class="subscription-manager">
        <div class="admin-tabs">
          <div class="admin-tab ${this.activeTab === 'plans' ? 'active' : ''}" 
               @click=${() => this.setActiveTab('plans')}>Plans</div>
          <div class="admin-tab ${this.activeTab === 'features' ? 'active' : ''}" 
               @click=${() => this.setActiveTab('features')}>Features</div>
          <div class="admin-tab ${this.activeTab === 'templates' ? 'active' : ''}" 
               @click=${() => this.setActiveTab('templates')}>Page Templates</div>
        </div>

        <div class="section">
          <div class="tab-content ${this.activeTab === 'plans' ? 'active' : ''}" id="plans-tab">
            <subscription-plans
              .plans=${this.plans}
              .features=${this.features}
              .loading=${this.loading}
              @plan-created=${this.handlePlanCreated}
              @plan-updated=${this.handlePlanUpdated}>
            </subscription-plans>
          </div>

          <div class="tab-content ${this.activeTab === 'features' ? 'active' : ''}" id="features-tab">
            <subscription-features
              .features=${this.features}
              .loading=${this.loading}
              @feature-created=${this.handleFeatureCreated}
              @feature-updated=${this.handleFeatureUpdated}>
            </subscription-features>
          </div>

          <div class="tab-content ${this.activeTab === 'templates' ? 'active' : ''}" id="templates-tab">
            <subscription-templates
              .templates=${this.templates}
              .loading=${this.loading}
              @template-created=${this.handleTemplateCreated}
              @template-updated=${this.handleTemplateUpdated}>
            </subscription-templates>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('subscription-manager', SubscriptionManager);
