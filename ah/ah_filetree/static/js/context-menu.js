import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class ContextMenu extends BaseEl {
  static styles = css`
    .context-menu {
      position: fixed;
      border: 1px solid #ccc;
      box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
      z-index: 1000;
      background-color: rgba(60,60,60,0.6);
      background-blur: 5px;
    }
    .menu-item {
      padding: 5px 10px;
      cursor: pointer;
    }
    .menu-item:hover {
      background-color: rgba(60,60,60,0.69);
    }
  `;

  constructor() {
    super();
    this.items = [];
    this.visible = false;
    this.x = 0;
    this.y = 0;
  }

  show(x, y, items) {
    console.log('Context menu activated'); // Added console log
    this.x = x;
    this.y = y;
    this.items = items;
    this.visible = true;
    this.requestUpdate();
    document.addEventListener('click', this.hide.bind(this));
  }

  hide() {
    this.visible = false;
    this.requestUpdate();
    document.removeEventListener('click', this.hide.bind(this));
  }

  handleItemClick(item) {
    item.action();
    this.hide();
  }

  _render() {
    if (!this.visible) return '';

    return html`
      <div class="context-menu" style="left: ${this.x}px; top: ${this.y}px;">
        ${this.items.map(item => html`
          <div class="menu-item" @click=${() => this.handleItemClick(item)}>${item.label}</div>
        `)}
      </div>
    `;
  }
}

customElements.define('context-menu', ContextMenu);
