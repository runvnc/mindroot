import {LitElement, html, css} from './lit-core.min.js';
import {BaseEl} from './base.js'

export class ChatMessage extends BaseEl {
  static properties = {
    sender: {type: String}
  }

  static styles = [ css`` ]

  constructor() {
    super()
    this.sender = 'user'
  }


  _render() {
    return html`
    <div class="message ${this.sender}">
      <slot></slot>
    </div>
  `
  }
}

customElements.define('chat-message', ChatMessage)

