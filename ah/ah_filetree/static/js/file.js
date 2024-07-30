import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class File_ extends BaseEl {
  static properties = {
    name: { type: String },
    path: { type: String }
  };

  static styles = css`
    .file {
      padding: 5px;
      cursor: pointer;
    }
    .file:hover {
      background-color: #f0f0f0;
    }
  `;

  constructor() {
    super();
    this.name = '';
    this.path = '';
  }

  _render() {
    return html`
      <div class="file" @click=${this.handleClick}>
        ${this.name}
      </div>
    `;
  }

  handleClick() {
    this.dispatch('file-selected', { name: this.name, path: this.path });
  }
}

customElements.define('file-', File_);
