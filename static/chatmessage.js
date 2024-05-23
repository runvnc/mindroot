import {LitElement, html} from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js'

class ChatMessage extends Base {
  static properties = {
    sender: {type: String}
  }

  constructor() {
    super()
    this.sender = 'user'
  }

  render() {
    let cls = ''
    if (this.sender == 'user') cls = 'bg-blue-200', 'text-left'
    else cls = 'bg-yellow-200', 'text-right'

    return html`
    <div class="message p-2 my-1 rounded ${cls}">
      <slot></slot>
    </div>
  `
}

element('chat-message', ChatMessage)


