import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class SubDir extends BaseEl {
  static properties = {
    dir: { type: String },
    path: { type: String },
    collapsed: { type: Boolean }
  };

  static styles = css`
    .sub-dir {
      margin-left: 20px;
    }
    .dir-name {
      cursor: pointer;
      padding: 5px;
    }
    .dir-name:hover {
      background-color: #f0f0f0;
    }
  `;

  constructor() {
    super();
    this.dir = '';
    this.path = '';
    this.collapsed = false;
  }

  _render() {
    return html`
      <div class="sub-dir">
        <div class="dir-name" @click=${this.toggleCollapse}>
          ${this.collapsed ? '▶' : '▼'} ${this.dir}
        </div>
        ${this.collapsed ? '' : html`<slot></slot>`}
      </div>
    `;
  }

  toggleCollapse() {
    this.collapsed = !this.collapsed;
    this.dispatch('dir-toggled', { dir: this.dir, path: this.path, collapsed: this.collapsed });
  }
}

customElements.define('sub-dir', SubDir);
