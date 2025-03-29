import { LitElement, html, css } from './lit-core.min.js'
import {BaseEl} from './base.js'
import {isMobile} from './ismobile.js'
import { authenticatedFetch } from './authfetch.js';

// show in bright orange in the console
console.log('%cChatForm loaded', 'color: orange; font-weight: bold;')

class ChatForm extends BaseEl {
  static properties = {
    sender: { type: String },
    message: { type: String },
    taskid: { type: String },
    autoSizeInput: { type: Boolean, attribute: 'auto-size-input', reflect: true }
  }
  
  static styles = [
    css`
      .message-input {
        min-height: 5em;
        border-radius: 0;
        border: 1px solid #444;
        max-height: 40em;
        overflow-y: hidden;
        box-sizing: border-box;
        flex: 9;
        width: auto;
        height: 140px;
        flex-shrink: 1;
        padding-right: 75px; /* Increased space */
      }
      .message-container {
        height: 145px;
        display: flex;
        position: relative;
        align-items: flex-end;
      }

      button {
        border-radius: 0;
        border: none;
        height: 40px;
        width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;
        flex-shrink: 0;
      }
      
      .send_msg {
        position: absolute;
        right: 21px; /* Original optimal position */
        margin-right: 5px;
        bottom: 15px; /* Raised 5px to prevent bottom overlap */
        /* background: transparent; */
        background-color: #101020

        border: none; /* 1px solid #444; */
        border-left: none;
      }
      .stop-button {
        position: absolute;
        margin-right: 5px;
        right: 61px; /* Maintains 40px spacing from send button */
        bottom: 15px; /* Matches send button exactly */
        background: #ff4d4d;
        color: white;
        border: none;
      }


      .image-preview-container {
        display: none;
        margin-bottom: 10px;
      }
      .image-preview-container.has-images {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .preview-thumbnail {
        position: relative;
        width: 100px;
        height: 100px;
        border-radius: 4px;
        overflow: hidden;
      }
      .preview-thumbnail img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        cursor: pointer;
      }
      .remove-image {
        position: absolute;
        top: 4px;
        right: 4px;
        width: 24px;
        height: 24px;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        padding: 0;
      }
      .upload-container {
        display: flex;
        align-items: center;
        gap: 2px;
        flex: 0 0 70px;
        width: 70px;
      }
      .upload-button {
        background: none;
        border: none;
        padding: 0;
        cursor: pointer;
        color: inherit;
      }
      .upload-button:hover {
        opacity: 0.8;
      }
      #imageUpload {
        display: none;
      }
      .loading {
        opacity: 0.5;
        pointer-events: none;
      }
      .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      }
      .modal img {
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
      }
    `
  ]

  constructor() {
    super()
    this.sender = 'user'
    this.message = ''
    this.autoSizeInput = true
    this.taskid = null
    this.selectedImages = []
    this.isLoading = false
  }

  async _handlePaste(e) {
    const items = e.clipboardData.items
    for (let item of items) {
      if (item.type.indexOf('image') !== -1) {
        const blob = item.getAsFile()
        await this._processImage(blob)
      }
    }
  }

  async _handleUpload(e) {
    const files = e.target.files
    for (let file of files) {
      if (file.type.indexOf('image') === -1) {
        continue
      }
      await this._processImage(file)
    }
  }

  _resizeTextarea() {
    if (this.autoSizeInput) {
      const textarea = this.messageEl;
      textarea.style.height = 'auto';
      const newHeight = Math.min(Math.max(textarea.scrollHeight, 72), 640);
      if (textarea.clientHeight != newHeight) {
        console.log("height does not match. current height: ", textarea.style.height, " new height: ", `${newHeight}px`)
        textarea.style.height = `${newHeight}px`;
      }
      const container = this.shadowRoot.querySelector('.message-container');
      if (container && container.clientHeight != (newHeight + 5)) {
          container.style.height = (newHeight + 5) + 'px';
      }
      this.previousHeight = newHeight;
    }
  }

  async _processImage(file) {
    if (this.isLoading) return

    this.isLoading = true
    this.requestUpdate()

    try {
      const imageData = await this._readFileAsDataURL(file)
      this.selectedImages.push(imageData)
      this._updateImagePreviews()
    } catch (error) {
      console.error('Error processing image:', error)
    } finally {
      this.isLoading = false
      this.requestUpdate()
    }
  }

  _readFileAsDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = e => resolve(e.target.result)
      reader.onerror = e => reject(e.target.error)
      reader.readAsDataURL(file)
    })
  }

  _updateImagePreviews() {
    const container = this.shadowRoot.querySelector('.image-preview-container')
    container.innerHTML = ''
    
    if (this.selectedImages.length > 0) {
      container.classList.add('has-images')
      this.selectedImages.forEach((imageData, index) => {
        const preview = document.createElement('div')
        preview.className = 'preview-thumbnail'
        preview.innerHTML = `
          <img src="${imageData}" alt="preview">
          <button class="remove-image" data-index="${index}">\u00d7</button>
        `
        preview.querySelector('img').addEventListener('click', () => this._showFullImage(imageData))
        preview.querySelector('.remove-image').addEventListener('click', () => this._removeImage(index))
        container.appendChild(preview)
      })
    } else {
      container.classList.remove('has-images')
    }
  }

  _removeImage(index) {
    this.selectedImages.splice(index, 1)
    this._updateImagePreviews()
  }

  _showFullImage(imageData) {
    const modal = document.createElement('div')
    modal.className = 'modal'
    modal.innerHTML = `<img src="${imageData}">`
    modal.addEventListener('click', () => modal.remove())
    document.body.appendChild(modal)
  }
  
  firstUpdated() {
    this.messageEl = this.shadowRoot.getElementById('inp_message');
    this.sendButton = this.shadowRoot.querySelector('.send_msg');
    
    const observer = new MutationObserver(() => {
      const stopButton = this.shadowRoot.querySelector('.stop-button');
      if (stopButton) this._resizeTextarea();
    });
    observer.observe(this.shadowRoot, { childList: true, subtree: true });
    
    this.messageEl.value = '';   
    this.messageEl.addEventListener('input', () => this._resizeTextarea());
    new ResizeObserver(() => this._resizeTextarea()).observe(this.messageEl);
  }

  async _cancelChat() {
    if (this.taskid) {
      const response = await authenticatedFetch(`/chat/${window.log_id}/${this.taskid}/cancel`, {
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

  async _send(event) {
    console.log("in _send")
    if (this.isLoading) return
    
    const messageContent = []
    console.log("..")
    if (this.messageEl.value.trim()) {
      messageContent.push({
        type: 'text',
        text: this.messageEl.value.replaceAll("\n", "\n\n")
      })
    }
    
    for (let imageData of this.selectedImages) {
      messageContent.push({
        type: 'image',
        data: imageData
      })
    }
   
    console.log({messageContent})
    if (messageContent.length === 0) return
    
    const ev_ = {
      content: messageContent,
      sender: 'user',
      persona: 'user'
    }
    
    this.dispatch('addmessage', ev_)
    this.messageEl.value = ''
    this.selectedImages = []
    this._updateImagePreviews()
    this._resizeTextarea()
    this.requestUpdate()
  }

  _render() {
    return html`
      <div id="chat-insert-top"></div>

      <div class="chat-entry flex py-2 ${this.isLoading ? 'loading' : ''}">
        <div class="message-container">
          <div class="image-preview-container"></div>
          <div class="upload-container">
            <label class="upload-button" title="Upload image">
              <input type="file" id="imageUpload" 
                     @change=${this._handleUpload} 
                     accept="image/*" multiple>
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14zm-5-7l-3 3.72L9 13l-3 4h12l-4-5z"/>
              </svg>
            </label>
          </div>
            <textarea id="inp_message" class="message-input"
              @keydown=${(e) => {
                if (!isMobile() && e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  this._send()
                }
              }}
              @paste=${this._handlePaste}
              required
            ></textarea>

        </div>
        <div id="chat-right-insert" style="display:none"></div>
        <button type="button" @click=${this._send} class="send_msg">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-2xl"><path fill-rule="evenodd" clip-rule="evenodd" d="M15.1918 8.90615C15.6381 8.45983 16.3618 8.45983 16.8081 8.90615L21.9509 14.049C22.3972 14.4953 22.3972 15.2189 21.9509 15.6652C21.5046 16.1116 20.781 16.1116 20.3347 15.6652L17.1428 12.4734V22.2857C17.1428 22.9169 16.6311 23.4286 15.9999 23.4286C15.3688 23.4286 14.8571 22.9169 14.8571 22.2857V12.4734L11.6652 15.6652C11.2189 16.1116 10.4953 16.1116 10.049 15.6652C9.60265 15.2189 9.60265 14.4953 10.049 14.049L15.1918 8.90615Z" fill="currentColor"></path></svg>
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
