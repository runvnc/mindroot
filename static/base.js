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
        super()
        const template = document
        .getElementById(`tmpl-${this.constructor.name}`)
        .content;
        const shadowRoot = this.attachShadow({mode: 'open'})
        .appendChild(template.cloneNode(true));
        console.log('Base constructor completed.')
      }

      sel(selector) {
        console.log({selector})
        selector = '*'
        return this.shadowRoot.querySelector(selector);
      }

      connectedCallback() {
        if (typeof this.connected === 'function') {
          this.connected();
        }
      }

      useTemplate(templateId) {
        const template = document.getElementById(templateId).content;
        console.log({template})
        //const clone = document.importNode(template, true);
        const clone = template.cloneNode(true);
        //const style = document.createElement('style');
        //style.textContent = `@import url('css/tailwind.css');`;
        //this.shadowRoot.appendChild(style);
        this.append(clone);
      }

      on(event, selector, handler) {
        setTimeout( () => {
          const element = this.sel(selector);
          console.log({element})
          console.log('skipping event attach')
          return
          if (element) {
            console.log('adding event listener', event, selector, handler)
            element.addEventListener(event, handler.bind(this));
          } else {
            throw new Error(`Could not connect event handler. Element not found: ${selector}`)
          }
        }, 100)
      }

      dispatch(event, detail) {
        this.dispatchEvent(new CustomEvent(event, { detail }));
      }
    }

function element(name, element) {
  customElements.define(name, element);
}
