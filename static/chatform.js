import { LitElement, html } from 'https://cdn.jsdelivr.net/gh/lit/dist@3/core/lit-core.min.js'


class ChatForm extends LitElement {
  static properties = {
    sender: { type: String },
    message: { type: String }
  }

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
  }


  _send(event) {
    console.log('send')
    const event = new Event('addmessage', {
      detail: {
        message: this.message,
        sender: this.sender
      },
      bubbles: true, 
      composed: true
    }) 
  }

  _senderChanged(event) {
    console.log('sender changed')
    this.sender = event.target.value
  }

  _messageChanged(event) {
    console.log('message changed')
    this.message = event.target.value
  }

  render() {
    return html`
      <div class="chat-entry flex py-2">
      <input type="text" class="message-input mr-2" @change={this._messageChanged} placeholder="Type a message..." required>
      <select @change={this._senderChanged} class="sender-select mr-2">
        <option value="user">User</option>
        <option value="ai">AI</option>
      </select>
      <button type="button" @click=${this.send} class="mr-2">Send</button>
      </div>
    `
    } 

    customElements.define('chat-form', ChatForm)

