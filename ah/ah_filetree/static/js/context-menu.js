import { html, css, LitElement } from './lit-core.min.js';

export class ContextMenu extends LitElement {
  static properties = {
    x: { type: Number },
    y: { type: Number },
    visible: { type: Boolean },
    items: { type: Array }
  };

  static styles = css`
    .context-menu {
      position: fixed;
      background: white;
      border: 1px solid #ccc;
      box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
      padding: 5px 0;
    }
    .menu-item {
      padding: 5px 20px;
      cursor: pointer;
    }
    .menu-item:hover {
      background-color: #f0f0f0;
    }
  `;

  constructor() {
    super();
    this.x = 0;
    this.y = 0;
    this.visible = false;
    this.items = [];
  }

  render() {
    if (!this.visible) return html``;
    
    return html`
      <div class="context-menu" style="left: ${this.x}px; top: ${this.y}px;">
        ${this.items.map(item => html`
          <div class="menu-item" @click=${() => this.handleItemClick(item)}>${item.label}</div>
        `)}
      </div>
    `;
  }

  handleItemClick(item) {
    this.dispatchEvent(new CustomEvent('menu-item-selected', { detail: item }));
    this.visible = false;
  }

  show(x, y, items) {
    this.x = x;
    this.y = y;
    this.items = items;
    this.visible = true;
  }

  hide() {
    this.visible = false;
  }
}

customElements.define('context-menu', ContextMenu);
