import { LitElement, html,css  } from './lit-core.min.js'
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
      <button type="button" @click=${this._send} class="send_msg"><!-- send msg (airplane) icon here -->
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-arrow-right" viewBox="0 0 16 16">
          <path fill-rule="evenodd" d="M11.354 8.354a.5.5 0 0 0 0-.708l-7-7a.5.5 0 0 0-.708.708L10.293 8l-6.647 6.646a.5.5 0 0 0 .708.708l7-7a.5.5 0 0 0 0-.708z"/>
          </svg>    
        </button>
      </div>
    `
    }

  }

  customElements.define('chat-form', ChatForm)

