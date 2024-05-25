import { LitElement, html, css } from './lit-core.min.js'
import { unsafeHTML } from 'https://unpkg.com/lit-html/directives/unsafe-html.js';
import { createContext } from 'lit/directives/context.js';

export const ThemeContext = createContext();

export class BaseEl extends LitElement {
  static properties = {
    theme: { type: String }
  }

  // Consume context to get the theme
  static get context() {
    return [[ThemeContext]];
  }

  constructor() {
    super();
    this.theme = 'default'; // Set a default theme if none is provided
  }

  /**
    super();    
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

  // Override to provide context to descendants
  provideContext() {
    return [[ThemeContext, this.theme]];
  }

  _render() {
    return html `
      <link rel="stylesheet" href="/static/css/${this.theme}.css">
      ` + this.render();
  }

}

