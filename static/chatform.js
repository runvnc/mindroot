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
    console.log('chatform constructor')
  }


  _send(event) {
    console.log('send')
    const ev_ = new CustomEvent('addmessage', {
      detail: {
        message: this.messageEl.value,
        sender: this.senderEl.value
      },
      bubbles: true, 
      composed: true
    })
    this.dispatchEvent(ev_)
  }

  firstUpdated() {
    console.log('chatform firstUpdated')
    this.senderEl = this.shadowRoot.getElementById('sel_sender')
    this.messageEl = this.shadowRoot.getElementById('inp_message')
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
      <input type="text" id="inp_message" class="message-input mr-2" @input=${this._messageChanged} placeholder="Type a message..." required>
      <select @select=${this._senderChanged} id="sel_sender" class="sender-select mr-2">
        <option value="user">User</option>
        <option value="ai">AI</option>
      </select>
      <button type="button" @click=${this._send} class="mr-2">Send</button>
      </div>
    `
    }

  }

  customElements.define('chat-form', ChatForm)

