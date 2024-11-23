import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './plugin-list.js';
import './plugin-index-browser.js';
import './plugin-advanced-install.js';

class PluginManager extends BaseEl {
  static styles = css`
    .plugin-manager {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 20px;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section-title {
      font-size: 1.2em;
      font-weight: bold;
      margin-bottom: 15px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .section-title .material-icons {
      font-size: 1.2em;
      opacity: 0.8;
    }

    .divider {
      height: 1px;
      background: rgba(255, 255, 255, 0.1);
      margin: 20px 0;
    }
  `;

  constructor() {
    super();
    this.addEventListener('plugin-installed', () => this.handlePluginChange());
    this.addEventListener('plugins-scanned', () => this.handlePluginChange());
  }

  handlePluginChange() {
    // Refresh all plugin lists
    const lists = this.shadowRoot.querySelectorAll('plugin-list');
    lists.forEach(list => list.fetchPlugins());
  }

  _render() {
    return html`
      <div class="plugin-manager">
        <section class="section">
          <div class="section-title">
            <span class="material-icons">extension</span>
            Installed Plugins
          </div>
          <plugin-list category="core"></plugin-list>
          <div class="divider"></div>
          <plugin-list category="installed"></plugin-list>
        </section>

        <section class="section">
          <div class="section-title">
            <span class="material-icons">store</span>
            Plugin Indices
          </div>
          <plugin-index-browser></plugin-index-browser>
        </section>

        <section class="section">
          <div class="section-title">
            <span class="material-icons">build</span>
            Advanced Installation
          </div>
          <plugin-advanced-install></plugin-advanced-install>
        </section>
      </div>
    `;
  }
}

customElements.define('plugin-manager', PluginManager);
