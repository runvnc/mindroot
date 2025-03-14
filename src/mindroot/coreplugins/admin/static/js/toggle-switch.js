import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

class ToggleSwitch extends BaseEl {
  static properties = {
    checked: { type: Boolean, reflect: true },
    id: { type: String }
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

  constructor() {
    super();
    this.checked = false;
    this.id = '';
  }

  updated(changedProperties) {
    
    if (changedProperties.has('checked')) {
      // Ensure the input element's checked state matches the property
      const input = this.shadowRoot.querySelector('input');
      console.log(`Updating toggle-switch ${this.id} to ${this.checked}`);
      if (input && input.checked !== this.checked) {
        input.checked = this.checked;
      }
    }
  }

  _render() {
    return html`
      <label class="switch">
        <input type="checkbox" 
               id="${this.id}"
               ?checked=${this.checked} 
               @change=${this._handleChange}>
        <span class="slider"></span>
      </label>
    `;
  }

  _handleChange(event) {
    const newChecked = event.target.checked;
    console.log(`Toggle switch ${this.id} changed to ${newChecked}`);
    if (this.checked !== newChecked) {
      this.checked = newChecked;
      this.dispatchEvent(new CustomEvent('toggle-change', { 
        detail: { 
          checked: this.checked,
          id: this.id,
          source: 'toggle-switch'
        },
        bubbles: false,
        composed: true
      }));
    }
  }
}

customElements.define('toggle-switch', ToggleSwitch);
