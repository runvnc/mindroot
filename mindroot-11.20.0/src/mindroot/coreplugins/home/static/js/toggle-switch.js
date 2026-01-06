import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class ToggleSwitch extends BaseEl {
  static properties = {
    checked: { type: Boolean }
  };

  static styles = css`
    .switch {
      position: relative;
      display: inline-block;
      width: 60px;
      height: 34px;
    }

    .switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: #ccc;
      transition: .4s;
      border-radius: 34px;
    }

    .slider:before {
      position: absolute;
      content: "";
      height: 26px;
      width: 26px;
      left: 4px;
      bottom: 4px;
      background-color: white;
      transition: .4s;
      border-radius: 50%;
    }

    input:checked + .slider {
      background-color: #2196F3;
    }

    input:checked + .slider:before {
      transform: translateX(26px);
    }
  `;

  render() {
    return html`
      <label class="switch">
        <input type="checkbox" .checked=${this.checked} @change=${this._handleChange}>
        <span class="slider"></span>
      </label>
    `;
  }

  _handleChange(event) {
    this.checked = event.target.checked;
    console.log("check is", this.checked)
    this.dispatch('toggle-change', { checked: this.checked });
  }
}

customElements.define('toggle-switch', ToggleSwitch);
