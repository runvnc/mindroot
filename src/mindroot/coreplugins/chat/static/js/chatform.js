import { LitElement, html, css } from './lit-core.min.js'
import {BaseEl} from './base.js'
import {isMobile} from './ismobile.js'

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
      .image-preview-container {
        display: none;
      }
      .image-preview-container.has-images {
        display: flex;
      }
    `
  ]

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
    this.taskid = null
    this.pastedImages = []
    console.log('chatform constructor')
    console.log('theme = ', this.theme)
  }

  async _handlePaste(e) {
    console.log("paste detected")
    const items = e.clipboardData.items;
    let hasImage = false;

    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        console.log("found image")
        hasImage = true;
        const blob = item.getAsFile();
        const reader = new FileReader();
        
        reader.onload = (e) => {
          this.pastedImages.push(e.target.result);
          this._updateImagePreviews();
        };
        
        reader.readAsDataURL(blob);
      }
    }
  }

  _updateImagePreviews() {
    const container = this.shadowRoot.querySelector('.image-preview-container');
    container.innerHTML = '';
    
    if (this.pastedImages.length > 0) {
      container.classList.add('has-images');
      this.pastedImages.forEach((imageData, index) => {
        const preview = document.createElement('div');
        preview.className = 'preview-thumbnail';
        preview.innerHTML = `
          <img src="${imageData}" alt="preview">
          <button class="remove-image" data-index="${index}">×</button>
        `;
        preview.querySelector('.remove-image').addEventListener('click', () => this._removeImage(index));
        container.appendChild(preview);
      });
    } else {
      container.classList.remove('has-images');
    }
    this.requestUpdate();
  }

  _removeImage(index) {
    this.pastedImages.splice(index, 1);
    this._updateImagePreviews();
  }

  async _send(event) {
    console.log('send')
    const messageContent = [];
    
    // Add text content if present
    if (this.messageEl.value.trim()) {
      messageContent.push({
        type: 'text',
        text: this.messageEl.value.replaceAll("\n", "\n\n")
      });
    }
    
    // Add any images
    for (let imageData of this.pastedImages) {
      console.log('adding pasted image')
      messageContent.push({
        type: 'image',
        data: imageData
      });
    }
    
    const ev_ = {
      content: messageContent,
      sender: 'user',
      persona: 'user'
    }
    
    this.dispatch('addmessage', ev_)
    this.messageEl.value = ''
    this.pastedImages = []
    this._updateImagePreviews()
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
    textarea.style.height = 'auto';
    // Set the height to the scrollHeight
    const newHeight = Math.min(Math.max(textarea.scrollHeight, 72), 640); // 3em to 40em
    textarea.style.height = `${newHeight}px`;
    this.requestUpdate();
    console.log('resize')
  }

  firstUpdated() {
    this.messageEl = this.shadowRoot.getElementById('inp_message');
    this.messageEl.value = '';
    this.messageEl.addEventListener('input', () => this._resizeTextarea());
    this.messageEl.addEventListener('paste', (e) => this._handlePaste(e));
    // Initial resize
    this._resizeTextarea();
    // Use ResizeObserver for more consistent behavior
    new ResizeObserver(() => this._resizeTextarea()).observe(this.messageEl);
  }

  _render() {
    return html`
      <div class="chat-entry flex py-2">
        <div class="message-container">
          <div class="image-preview-container"></div>
          <textarea id="inp_message" class="message-input"
            rows="4" 
            @keydown=${(e) => {
              if (!isMobile() && e.key === 'Enter') {
                if (!e.shiftKey) {
                  e.preventDefault();
                  this._send();
                }
              }
            }}
            @input=${this._messageChanged}
            required
          ></textarea>
        </div>
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
