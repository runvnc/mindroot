import {LitElement, html, css} from './lit-core.min.js';
import {BaseEl} from './base.js'

export class ChatMessage extends BaseEl {
  static properties = {
    sender: {type: String}
  }

  static styles = [
    css`
    .user {
      text-align: left;
      color: blue;
    }

    .ai {
      text-align: right;
      color: yellow; 
    }

  `
  ]

  constructor() {
    super()
    this.sender = 'user'
  }

  render() {
    return html`
    <div class="message p-2 my-1 rounded ${this.sender}">
      <slot></slot>
    </div>
  `
  }
}

customElements.define('chat-message', ChatMessage)

