    class TElement extends HTMLElement {
      constructor() {
        super();
        const template = document.createElement('template');
        template.innerHTML = this.innerHTML;
        this._content = template.content;
      }

      get content() {
        return this._content;
      }
    }

    customElements.define('t-', TElement);

    class Base extends HTMLElement {
      constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        const templateId = `tmpl-${this.constructor.name}`;
        this.useTemplate(templateId);
      }

      sel(selector) {
        return this.shadowRoot.querySelector(selector);
      }

      connectedCallback() {
        if (typeof this.connected === 'function') {
          this.connected();
        }
      }

      useTemplate(templateId) {
        const template = document.getElementById(templateId).content;
        const clone = document.importNode(template, true);
        const style = document.createElement('style');
        style.textContent = `@import url('css/tailwind.css');`;
        this.shadowRoot.appendChild(style);
        this.shadowRoot.appendChild(clone);
      }

      on(event, selector, handler) {
        const element = this.sel(selector);
        if (element) {
          element.addEventListener(event, handler.bind(this));
        }
      }

      dispatch(event, detail) {
        this.dispatchEvent(new CustomEvent(event, { detail }));
      }
    }

function element(name, element) {
  customElements.define(name, element);
}
