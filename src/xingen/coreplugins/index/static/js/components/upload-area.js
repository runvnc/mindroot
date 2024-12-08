import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';

class UploadArea extends LitElement {
  static properties = {
    loading: { type: Boolean },
    error: { type: String },
    dragActive: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      margin-bottom: 1rem;
    }

    .upload-area {
      border: 2px dashed rgba(255, 255, 255, 0.2);
      border-radius: 8px;
      padding: 1.5rem;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s ease;
      background: rgba(0, 0, 0, 0.2);
    }

    .upload-area:hover {
      border-color: rgba(255, 255, 255, 0.4);
      background: rgba(0, 0, 0, 0.3);
    }

    .upload-area.drag-active {
      border-color: #3498db;
      background: rgba(52, 152, 219, 0.1);
    }

    .upload-area.loading {
      border-color: #f1c40f;
      cursor: wait;
    }

    .upload-area.error {
      border-color: #e74c3c;
    }

    .error-message {
      color: #e74c3c;
      margin-top: 0.5rem;
      font-size: 0.9rem;
    }

    .loading-spinner {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 2px solid #f1c40f;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s linear infinite;
      margin-right: 0.5rem;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `;

  constructor() {
    super();
    this.loading = false;
    this.error = '';
    this.dragActive = false;
    this.setupDragAndDrop();
  }

  setupDragAndDrop() {
    this.addEventListener('dragenter', this.handleDragIn);
    this.addEventListener('dragleave', this.handleDragOut);
    this.addEventListener('dragover', this.handleDragOver);
    this.addEventListener('drop', this.handleDrop);
  }

  handleDragIn(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dragActive = true;
  }

  handleDragOut(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dragActive = false;
  }

  handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  async handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.dragActive = false;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  async handleFile(file) {
    if (!file.name.endsWith('.zip')) {
      this.error = 'Please upload a zip file';
      return;
    }

    this.loading = true;
    this.error = '';

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/index/install-zip', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('index-installed', {
          detail: { message: result.message }
        }));
      } else {
        this.error = result.message || 'Failed to install index';
      }
    } catch (error) {
      console.error('Error installing index:', error);
      this.error = 'Failed to install index';
    } finally {
      this.loading = false;
    }
  }

  handleClick() {
    const input = this.shadowRoot.querySelector('#fileInput');
    input.click();
  }

  render() {
    return html`
      <div class="upload-area ${this.dragActive ? 'drag-active' : ''} 
                              ${this.loading ? 'loading' : ''}
                              ${this.error ? 'error' : ''}"
           @click=${this.handleClick}>
        <input type="file" id="fileInput" style="display: none" accept=".zip"
               @change=${(e) => this.handleFile(e.target.files[0])}>
        ${this.loading ? html`
          <div class="loading-spinner"></div>
          <span>Installing index...</span>
        ` : html`
          <span>Drop a zip file here or click to upload an index</span>
        `}
      </div>
      ${this.error ? html`
        <div class="error-message">${this.error}</div>
      ` : ''}
    `;
  }
}

customElements.define('upload-area', UploadArea);
