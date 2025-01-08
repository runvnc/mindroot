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
        gap: 8px;
      }
      .upload-button {
        background: none;
        border: none;
        padding: 8px;
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
    //e.target.value = '' // Reset file input
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
          <button class="remove-image" data-index="${index}">×</button>
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
    this.messageEl.value = '';
    new ResizeObserver(() => this._resizeTextarea()).observe(this.messageEl);
  }


  async _send(event) {
    if (this.isLoading) return
    
    const messageContent = []
    
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
            <textarea id="inp_message" class="message-input"
              rows="4" 
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
