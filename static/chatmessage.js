import {LitElement, html, css} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js'
//import {LitElement, html} from 'lit-core.min.js';


export class ChatMessage extends LitElement {
  static properties = {
    sender: {type: String}
  }

  static styles = css`

    :host {
      display: block;
      background-color: black;
      color: white;
    }

    .user {
      text-align: left;
      color: blue;
    }

    .ai {
      text-align: right;
      color: yellow; 
    }

  `

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

