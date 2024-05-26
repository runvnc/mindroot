import { LitElement, html,css  } from '/static/js/lit-core.min.js'
import {BaseEl} from './base.js'

class ChatForm extends BaseEl {
  static properties = {
    sender: { type: String },
    message: { type: String }
  }
  
  static styles = [
    css`
  `]

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
    console.log('chatform constructor')
    console.log('theme = ', this.theme)
  }

  _send(event) {
    console.log('send')
    const ev_ = {
        content: this.messageEl.value,
        sender: 'user',
        persona: 'user'
    }
    this.dispatch('addmessage', ev_)
    this.messageEl.value = ''
  }

  firstUpdated() {
    this.messageEl = this.shadowRoot.getElementById('inp_message')
    this.messageEl.value = ''
  }

 _render() {
    return html`
      <div class="chat-entry flex py-2">
      <textarea rows="3" columns="80" id="inp_message" class="message-input"
        @keydown=${(e) => {if (e.keyCode === 13) this._send()}} 
        @input=${this._messageChanged} required></textarea>
      <button type="button" @click=${this._send} class="mr-2">Send</button>
      </div>
    `
    }

  }

  customElements.define('chat-form', ChatForm)

