import { LitElement, html, css } from './lit-core.min.js'
import {BaseEl} from './base.js'

class ChatForm extends BaseEl {
  static properties = {
    sender: { type: String },
    message: { type: String },
    taskid: { type: String }
  }
  
  static styles = [
    css`
      .message-input {
        min-height: 3em;
        max-height: 40em;
        resize: none;
        overflow-y: hidden;
        box-sizing: border-box;
        width: 93%;
      }
      .stop-button {
        color: white;
        border: none;
        padding: 8px;
        margin-left: 5px;
        cursor: pointer;
      }
      .stop-button svg {
        width: 24px;
        height: 24px;
      }
    `
  ]

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
    this.taskid = null
    console.log('chatform constructor')
    console.log('theme = ', this.theme)
  }

  async _send(event) {
    console.log('send')
    const ev_ = {
        content: this.messageEl.value,
        sender: 'user',
        persona: 'user'
    }
    this.dispatch('addmessage', ev_)
    this.messageEl.value = ''
    this._resizeTextarea() // Reset size after sending
    this.requestUpdate()
  }

  async _cancelChat() {
    if (this.taskid) {
      const response = await fetch(`/chat/${window.log_id}/${this.taskid}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ task_id: this.taskid }),
      })
      const data = await response.json()
      console.log('Chat cancelled:', data)
      this.taskid = null
      setTimeout(() => {
       this.requestUpdate()
      },500)
    }
  }

  _resizeTextarea() {
    const textarea = this.messageEl;
    // Reset height to auto to get the correct scrollHeight
    console.log({textarea})
    textarea.style.height = 'auto';
    // Set the height to the scrollHeight
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 48), 640); // 3em to 40em
    console.log('scrollHeight', textarea.scrollHeight)
    console.log('newHeight', newHeight)
    textarea.style.height = `${newHeight}px`;
    console.log('textarea.style.height', textarea.style.height)
    this.requestUpdate();
    console.log('resize')
  }

  firstUpdated() {
    this.messageEl = this.shadowRoot.getElementById('inp_message');
    this.messageEl.value = '';
    this.messageEl.addEventListener('input', () => this._resizeTextarea());
    // Initial resize
    this._resizeTextarea();
    // Use ResizeObserver for more consistent behavior
    new ResizeObserver(() => this._resizeTextarea()).observe(this.messageEl);
  }

  _render() {
    return html`
      <div class="chat-entry flex py-2">
        <textarea id="inp_message" class="message-input"
          @keydown=${(e) => {
            if (e.key === 'Enter') {
              if (!e.shiftKey) {
                e.preventDefault();
                this._send();
              }
            }
          }}
          @input=${this._messageChanged}
          required
        ></textarea>
        <button type="button" @click=${this._send} class="send_msg">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" class="bi bi-arrow-right" viewBox="0 0 16 16">
            <path fill-rule="evenodd" d="M11.354 8.354a.5.5 0 0 0 0-.708l-7-7a.5.5 0 0 0-.708.708L10.293 8l-6.647 6.646a.5.5 0 0 0 .708.708l7-7a.5.5 0 0 0 0-.708z"/>
          </svg>    
        </button>
        ${this.taskid ? html`
          <button type="button" @click=${this._cancelChat} class="stop-button">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 16 16">
              <rect width="10" height="10" x="3" y="3"/>
            </svg>
          </button>
        ` : ''}
      </div>
    `
  }
}

customElements.define('chat-form', ChatForm)
