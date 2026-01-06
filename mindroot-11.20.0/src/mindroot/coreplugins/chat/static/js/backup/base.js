import { LitElement, html, css } from './lit-core.min.js'
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';

export class BaseEl extends LitElement {
  static properties = {
    theme: { type: String }
  }

  constructor() {
    super();
    this.theme = window.theme ? window.theme : 'default'
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

  render() {
    return html`
      <link rel="stylesheet" href="/static/css/${this.theme}.css">
      ${this._render()}
    `;
  }

}

