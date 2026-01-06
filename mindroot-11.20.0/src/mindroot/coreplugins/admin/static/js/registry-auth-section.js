/**
 * Registry Authentication Section
 * 
 * Handles authentication UI and logic including login, registration,
 * and user management for the registry manager.
 */

import { html } from '/admin/static/js/lit-core.min.js';

class RegistryAuthSection {
  constructor(sharedState, mainComponent) {
    this.state = sharedState;
    this.main = mainComponent;
    this.services = null; // Will be set by main component
  }

  setServices(services) {
    this.services = services;
  }

  // === Event Handlers ===

  async handleLogin() {
    const username = this.main.shadowRoot.getElementById('username').value;
    const password = this.main.shadowRoot.getElementById('password').value;
    
    if (!username || !password) {
      this.services.showToast('Please enter username and password', 'error');
      return;
    }
    
    const success = await this.services.login(username, password);
    if (success) {
      this.main.requestUpdate();
    }
  }

  async handleRegister() {
    const username = this.main.shadowRoot.getElementById('reg-username').value;
    const email = this.main.shadowRoot.getElementById('reg-email').value;
    const password = this.main.shadowRoot.getElementById('reg-password').value;
    
    if (!username || !email || !password) {
      this.services.showToast('Please fill in all registration fields', 'error');
      return;
    }
    
    const success = await this.services.register(username, email, password);
    if (success) {
      this.main.showRegisterForm = false;
      this.main.requestUpdate();
    }
  }

  toggleRegisterForm() {
    this.main.showRegisterForm = !this.main.showRegisterForm;
    this.main.requestUpdate();
  }

  logout() {
    this.services.logout();
    this.main.requestUpdate();
  }

  // === Render Methods ===

  renderHeader() {
    if (this.state.isLoggedIn) {
      return this.renderLoggedInHeader();
    } else {
      return this.renderLoginForm();
    }
  }

  renderLoggedInHeader() {
    return html`
      <div class="user-info">
        <span>Logged in as: ${this.state.currentUser?.username}</span>
        <button @click=${() => this.logout()}>Logout</button>
      </div>
    `;
  }

  renderLoginForm() {
    if (this.main.showRegisterForm) {
      return this.renderRegistrationForm();
    } else {
      return this.renderLoginSection();
    }
  }

  renderLoginSection() {
    return html`
      <div class="section">
        <h3>Registry Login</h3>
        <div class="login-form">
          <input type="text" placeholder="Username or Email" id="username">
          <input type="password" placeholder="Password" id="password">
          <button class="primary" @click=${() => this.handleLogin()} ?disabled=${this.state.loading}>
            ${this.state.loading ? 'Logging in...' : 'Login'}
          </button>
          ${this.main.error ? html`<div class="error">${this.main.error}</div>` : ''}
        </div>
        <div class="auth-toggle">
          <button @click=${() => this.toggleRegisterForm()}>Don't have an account? Register</button>
        </div>
      </div>
    `;
  }

  renderRegistrationForm() {
    return html`
      <div class="section">
        <h3>Create Account</h3>
        <div class="login-form">
          <input type="text" placeholder="Username" id="reg-username">
          <input type="email" placeholder="Email" id="reg-email">
          <input type="password" placeholder="Password" id="reg-password">
          <button class="primary" @click=${() => this.handleRegister()} ?disabled=${this.state.loading}>
            ${this.state.loading ? 'Creating Account...' : 'Create Account'}
          </button>
          ${this.main.error ? html`<div class="error">${this.main.error}</div>` : ''}
        </div>
        <div class="auth-toggle">
          <button @click=${() => this.toggleRegisterForm()}>Already have an account? Login</button>
        </div>
      </div>
    `;
  }
}

export { RegistryAuthSection };