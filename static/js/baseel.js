// BaseEl.js
import { LitElement } from './lit-core.min.js';
import { sharedStyleSheet } from './shared-styles.js';

export class BaseEl extends LitElement {
  static get styles() {
    return [sharedStyleSheet];
  }

  /**
   * Abbreviation for this.shadowRoot.querySelector
   * @param {string} selector
   * @returns {Element|null}
   */
  getEl(selector) {
    return this.shadowRoot.querySelector(selector);
  }

  /**
   * Convenience method for dispatching custom events
   * @param {string} name
   * @param {any} detail
   * @param {boolean} [bubbles=true]
   * @param {boolean} [composed=true]
   */
  dispatch(name, detail, bubbles = true, composed = true) {
    this.dispatchEvent(new CustomEvent(name, {
      detail,
      bubbles,
      composed
    }));
  }
}

