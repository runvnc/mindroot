import { LitElement, html,css  } from '/static/js/lit-core.min.js'
import {BaseEl} from './base.js'

class ChatForm extends BaseEl {
  static properties = {
    sender: { type: String },
    message: { type: String }
  }
  
  static styles = [
    css`
    .message-input {
      background-color: #030303;
      color: #f0f0f0;
    }

  `]

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
    console.log('chatform constructor')
  }

  _send(event) {
    console.log('send')
    const ev_ = {
        content: this.messageEl.value,
        sender: this.senderEl.value
    }
    this.dispatch('addmessage', ev_)
  }

  firstUpdated() {
    console.log('chatform firstUpdated')
    this.senderEl = this.shadowRoot.getElementById('sel_sender')
    this.messageEl = this.shadowRoot.getElementById('inp_message')
  }

  render() {
    return html`
      <div class="chat-entry flex py-2">
      <textarea type="text" id="inp_message" class="message-input" @input=${this._messageChanged} required></textarea>
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

