import { LitElement } from './lit-core.min.js';
import { loadStyles } from './load-styles.js';

export class BaseEl extends LitElement {
  static sharedStylesLoaded = false;
  static sharedStyles = new CSSStyleSheet();

  static async loadSharedStyles() {
    if (!BaseEl.sharedStylesLoaded) {
      BaseEl.sharedStyles = await loadStyles('/static/css/main.css');
      BaseEl.sharedStylesLoaded = true;
    }
  }

  constructor() {
    super();
      BaseEl.loadSharedStyles().then(() => {
        try {
          this.constructor.styles = [
            ...this.constructor.styles,
            BaseEl.sharedStyles
          ];
        this.requestUpdate();
      } catch (e) {
        console.error('Error loading styles: ' + JSON.stringify(e, null, 4) + ' \n\n' + this.constructor.name);
      }
    });
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

