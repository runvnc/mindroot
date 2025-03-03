/**
 * Subscriptions plugin frontend functionality
 */

class SubscriptionManager {
  constructor() {
    this.initialized = false;
    this.plans = [];
    this.userSubscriptions = [];
  }

  async initialize() {
    if (this.initialized) return;
    
    try {
      await this.loadPlans();
      await this.loadUserSubscriptions();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize subscription manager:', error);
    }
  }

  async loadPlans() {
    try {
      const response = await fetch('/subscriptions/plans');
      const result = await response.json();
      
      if (result.status === 'success') {
        this.plans = result.plans;
      } else {
        console.error('Failed to load subscription plans:', result.message);
      }
    } catch (error) {
      console.error('Error loading subscription plans:', error);
    }
  }

  async loadUserSubscriptions() {
    try {
      const response = await fetch('/subscriptions/my');
      const result = await response.json();
      
      if (result.status === 'success') {
        this.userSubscriptions = result.subscriptions;
      } else {
        console.error('Failed to load user subscriptions:', result.message);
      }
    } catch (error) {
      console.error('Error loading user subscriptions:', error);
    }
  }

  async createCheckout(planId) {
    try {
      const response = await fetch(`/subscriptions/checkout/${planId}`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.status === 'success' && result.url) {
        window.location.href = result.url;
      } else {
        console.error('Failed to create checkout:', result.message);
        return null;
      }
    } catch (error) {
      console.error('Error creating checkout:', error);
      return null;
    }
  }

  async cancelSubscription(subscriptionId, atPeriodEnd = true) {
    try {
      const response = await fetch(`/subscriptions/cancel/${subscriptionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ at_period_end: atPeriodEnd })
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        // Refresh subscriptions
        await this.loadUserSubscriptions();
        return result.subscription;
      } else {
        console.error('Failed to cancel subscription:', result.message);
        return null;
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      return null;
    }
  }

  hasActiveSubscription() {
    return this.userSubscriptions.some(sub => 
      sub.status === 'active' && !sub.cancel_at_period_end
    );
  }

  getActivePlan() {
    const activeSub = this.userSubscriptions.find(sub => 
      sub.status === 'active' && !sub.cancel_at_period_end
    );
    
    if (!activeSub) return null;
    
    return this.plans.find(plan => plan.plan_id === activeSub.plan_id) || null;
  }

  renderSubscriptionInfo(elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    if (this.userSubscriptions.length === 0) {
      container.innerHTML = `
        <div class="subscription-info">
          <p>You don't have any active subscriptions.</p>
          <button class="btn btn-primary" onclick="showSubscriptionPlans()">
            View Subscription Plans
          </button>
        </div>
      `;
      return;
    }
    
    // Sort subscriptions with active ones first
    const sortedSubs = [...this.userSubscriptions].sort((a, b) => {
      if (a.status === 'active' && b.status !== 'active') return -1;
      if (a.status !== 'active' && b.status === 'active') return 1;
      return new Date(b.created_at) - new Date(a.created_at);
    });
    
    const subsHtml = sortedSubs.map(sub => {
      const plan = this.plans.find(p => p.plan_id === sub.plan_id) || {
        name: 'Unknown Plan',
        price: 0,
        currency: 'USD',
        interval: 'month'
      };
      
      const startDate = new Date(sub.current_period_start).toLocaleDateString();
      const endDate = new Date(sub.current_period_end).toLocaleDateString();
      
      let statusClass = 'status-inactive';
      if (sub.status === 'active') statusClass = 'status-active';
      if (sub.status === 'past_due') statusClass = 'status-warning';
      if (sub.status === 'canceled') statusClass = 'status-canceled';
      
      let cancelButton = '';
      if (sub.status === 'active' && !sub.cancel_at_period_end) {
        cancelButton = `
          <button class="btn btn-sm btn-danger" 
                  onclick="subscriptionManager.cancelSubscription('${sub.subscription_id}')">
            Cancel
          </button>
        `;
      }
      
      return `
        <div class="subscription-card">
          <div class="subscription-header">
            <div class="subscription-plan">${plan.name}</div>
            <div class="subscription-status ${statusClass}">${sub.status}</div>
          </div>
          
          <div class="subscription-details">
            <div class="subscription-price">
              ${plan.price} ${plan.currency}/${plan.interval}
            </div>
            
            <div class="subscription-period">
              Current period: ${startDate} - ${endDate}
            </div>
            
            ${sub.cancel_at_period_end ? 
              '<div class="subscription-cancel-notice">Will cancel at end of period</div>' : ''}
          </div>
          
          <div class="subscription-actions">
            ${cancelButton}
          </div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = `
      <div class="subscriptions-container">
        <h3>Your Subscriptions</h3>
        ${subsHtml}
      </div>
    `;
  }

  renderPlans(elementId) {
    const container = document.getElementById(elementId);
    if (!container) return;
    
    if (this.plans.length === 0) {
      container.innerHTML = '<p>No subscription plans available.</p>';
      return;
    }
    
    // Sort plans by price
    const sortedPlans = [...this.plans].sort((a, b) => a.price - b.price);
    
    const plansHtml = sortedPlans.map(plan => {
      return `
        <div class="plan-card">
          <div class="plan-header">
            <h3 class="plan-name">${plan.name}</h3>
            <div class="plan-price">
              ${plan.price} ${plan.currency}/${plan.interval}
            </div>
          </div>
          
          <div class="plan-description">${plan.description}</div>
          
          <div class="plan-features">
            <div class="plan-feature">
              <span class="feature-value">${plan.credits_per_cycle}</span> credits
              per ${plan.interval}
            </div>
            
            ${Object.entries(plan.features || {}).map(([key, value]) => `
              <div class="plan-feature">
                <span class="feature-name">${key}:</span>
                <span class="feature-value">${value}</span>
              </div>
            `).join('')}
          </div>
          
          <button class="btn btn-primary subscribe-btn" 
                  onclick="subscriptionManager.createCheckout('${plan.plan_id}')">
            Subscribe
          </button>
        </div>
      `;
    }).join('');
    
    container.innerHTML = `
      <div class="plans-container">
        <h3>Subscription Plans</h3>
        <div class="plans-grid">
          ${plansHtml}
        </div>
      </div>
    `;
  }
}

// Initialize global subscription manager
const subscriptionManager = new SubscriptionManager();

// Register command handler for subscription plans
window.registerCommandHandler('list_subscription_plans', (data) => {
  if (data.event === 'result') {
    return html`
      <div class="subscription-plans-result">
        <pre>${data.args}</pre>
      </div>
    `;
  }
  return null;
});

// Register command handler for user subscriptions
window.registerCommandHandler('get_my_subscriptions', (data) => {
  if (data.event === 'result') {
    return html`
      <div class="my-subscriptions-result">
        <pre>${data.args}</pre>
      </div>
    `;
  }
  return null;
});

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
  subscriptionManager.initialize();
});
