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
      gap: 0.75rem;
      width: 100%;
      max-width: 1600px;
      margin: 0 auto;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .section-title {
      font-size: 1.1rem;
      font-weight: 500;
      margin-bottom: 0.75rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .section-title .material-icons {
      font-size: 1.2rem;
      opacity: 0.8;
    }

    .divider {
      height: 1px;
      background: rgba(255, 255, 255, 0.1);
      margin: 0.75rem 0;
    }

    /* Core plugins collapsed by default */
    plugin-list[category="core"] {
      display: none;
    }

    .section details {
      margin-bottom: 0.75rem;
    }

    .section details summary {
      cursor: pointer;
      padding: 0.5rem;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      user-select: none;
    }

    .section details summary:hover {
      background: rgba(255, 255, 255, 0.08);
    }

    .section details[open] plugin-list[category="core"] {
      display: block;
      margin-top: 0.75rem;
    }

    .section details summary .material-icons.expand {
      transition: transform 0.2s ease;
    }

    .section details[open] summary .material-icons.expand {
      transform: rotate(90deg);
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

        <section class="section">
          <div class="section-title">
            <span class="material-icons">extension</span>
            Installed Plugins
          </div>
          <details>
            <summary>
              <span class="material-icons expand">chevron_right</span>
              <span class="material-icons">settings</span>
              Core Plugins
            </summary>
            <plugin-list category="core"></plugin-list>
          </details>
          <plugin-list category="installed"></plugin-list>
        </section>

      </div>
    `;
  }
}

customElements.define('plugin-manager', PluginManager);
