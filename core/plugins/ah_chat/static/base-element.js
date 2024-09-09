    class BaseElement extends HTMLElement {
      constructor() {
        super();
        this.attachShadow({ mode: 'open' });
      }

      sel(selector) {
        return this.shadowRoot.querySelector(selector);
      }

      useTemplate(templateId) {
        const template = document.getElementById(templateId);
        const clone = document.importNode(template.content, true);
        const style = document.createElement('style');
        style.textContent = `@import url('css/tailwind.css');`;
        this.shadowRoot.appendChild(style);
        this.shadowRoot.appendChild(clone);
      }
    }


