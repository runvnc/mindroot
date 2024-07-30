import { html, css, LitElement } from './lit-core.min.js';

export class FilePreview extends LitElement {
  static properties = {
    file: { type: Object }
  };

  static styles = css`
    .preview-container {
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 5px;
      max-width: 300px;
      max-height: 300px;
      overflow: auto;
    }
    img {
      max-width: 100%;
      max-height: 100%;
    }
    .text-preview {
      white-space: pre-wrap;
      font-family: monospace;
    }
  `;

  constructor() {
    super();
    this.file = null;
  }

  async firstUpdated() {
    if (this.file) {
      await this.loadPreview();
    }
  }

  async loadPreview() {
    if (!this.file) return;

    try {
      const response = await fetch(`/api/preview?path=${encodeURIComponent(this.file.path)}`);
      if (!response.ok) throw new Error('Failed to load preview');
      const data = await response.json();
      this.previewData = data.preview;
      this.requestUpdate();
    } catch (error) {
      console.error('Error loading preview:', error);
    }
  }

  renderPreview() {
    if (!this.file || !this.previewData) return html`<div>No preview available</div>`;

    const fileExtension = this.file.name.split('.').pop().toLowerCase();

    switch (fileExtension) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return html`<img src="data:image/${fileExtension};base64,${this.previewData}" alt="${this.file.name}">`;
      case 'txt':
      case 'md':
      case 'js':
      case 'py':
      case 'html':
      case 'css':
        return html`<pre class="text-preview">${this.previewData}</pre>`;
      case 'pdf':
        return html`<iframe src="data:application/pdf;base64,${this.previewData}" width="100%" height="300px"></iframe>`;
      default:
        return html`<div>Preview not supported for this file type</div>`;
    }
  }

  render() {
    return html`
      <div class="preview-container">
        ${this.file ? this.renderPreview() : 'Select a file to preview'}
      </div>
    `;
  }
}

customElements.define('file-preview', FilePreview);
