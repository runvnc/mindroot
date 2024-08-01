import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './file.js';
import './sub-dir.js';
import './context-menu.js';

export class FileTree extends BaseEl {
  static properties = {
    dir: { type: String },
    structure: { type: Object },
    error: { type: String },
    selectedItem: { type: Object },
    searchQuery: { type: String }
  };

  static styles = css`
    .file-tree {
      padding: 10px;
      font-size: 0.92em;
    }
    .file-tree.dragover {
      background-color: rgba(200, 200, 200, 0.1);
    }
    .error {
      color: red;
      padding: 10px;
    }
    .tree-container {
      max-height: 500px;
      overflow-y: auto;
    }
    .search-container {
      margin-bottom: 10px;
    }
    file-, sub-dir {
      display: block;
      font-size: 0.92em;
      padding: 2px 5px;
      cursor: pointer;
    }
    sub-dir {
      border-right: 1px solid #ccc;
    }
    file-:hover, sub-dir:hover {
      border: 1px solid #ccc;
    }
  `;

  constructor() {
    super();
    this.dir = '/';
    this.structure = null;
    this.error = '';
    this.selectedItem = null;
    this.searchQuery = '';
  }

  async firstUpdated() {
    await this.loadStructure();
    this.addEventListener('dragover', this.handleDragOver);
    this.addEventListener('dragleave', this.handleDragLeave);
    this.addEventListener('drop', this.handleDrop);
  }

  async loadStructure() {
    try {
      const response = await fetch(`/api/file-tree?dir=${encodeURIComponent(this.dir)}`);
      console.log({response})
      if (!response.ok) throw new Error('Failed to load file structure');
      this.structure = await response.json();
      this.error = '';
    } catch (error) {
      console.error('Error loading file structure:', error);
      this.error = 'Failed to load file structure. Please try again.';
    }
  }

  renderStructure(item) {
    if (this.searchQuery && !this.itemMatchesSearch(item)) return '';

    if (item.type === 'file') {
      return html`<file- name=${item.name} path=${item.path} 
        @file-selected=${this.handleFileSelected}
        @file-deleted=${this.handleFileDeleted}></file->`;
    } else if (item.type === 'directory') {
      return html`
        <sub-dir dir=${item.name} path=${item.path} ?collapsed=${item.collapsed} 
          @dir-toggled=${this.handleDirToggled}
          @dir-deleted=${this.handleDirDeleted}
          @new-file-created=${this.handleNewFileCreated}
          @new-folder-created=${this.handleNewFolderCreated}>
          ${item.children.map(child => this.renderStructure(child))}
        </sub-dir>
      `;
    }
  }

  itemMatchesSearch(item) {
    if (item.name.toLowerCase().includes(this.searchQuery.toLowerCase())) return true;
    if (item.type === 'directory') {
      return item.children.some(child => this.itemMatchesSearch(child));
    }
    return false;
  }

  handleFileSelected(e) {
    this.selectedItem = e.detail;
    this.dispatch('file-selected', this.selectedItem);
  }

  handleDirToggled(e) {
    this.selectedItem = e.detail;
    this.dispatch('dir-toggled', this.selectedItem);
  }

  handleFileDeleted(e) {
    console.log('File deleted:', e.detail.path);
    // Implement file deletion logic here
    // After successful deletion, reload the structure
    this.loadStructure();
  }

  handleDirDeleted(e) {
    console.log('Directory deleted:', e.detail.path);
    // Implement directory deletion logic here
    // After successful deletion, reload the structure
    this.loadStructure();
  }

  handleNewFileCreated(e) {
    console.log('New file created:', e.detail.path);
    // Implement new file creation logic here
    // After successful creation, reload the structure
    this.loadStructure();
  }

  handleNewFolderCreated(e) {
    console.log('New folder created:', e.detail.path);
    // Implement new folder creation logic here
    // After successful creation, reload the structure
    this.loadStructure();
  }

  handleSearchInput(e) {
    this.searchQuery = e.target.value;
  }

  handleDragOver(e) {
    e.preventDefault();
    this.classList.add('dragover');
  }

  handleDragLeave(e) {
    e.preventDefault();
    this.classList.remove('dragover');
  }

  handleDrop(e) {
    e.preventDefault();
    this.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      this.handleUpload({ target: { files } });
    }
  }

  handleUpload(e) {
    const files = e.target.files;
    if (files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('dir', this.dir);

    fetch('/api/upload', {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      console.log('Upload successful:', data);
      this.loadStructure();
    })
    .catch(error => {
      console.error('Error uploading file:', error);
    });
  }

  _render() {
    return html`
      <div class="file-tree">
        <div class="tree-container">
          ${this.error ? html`<div class="error">${this.error}</div>` : ''}
          <div class="search-container">
            <input type="text" placeholder="Search files..." @input=${this.handleSearchInput}>
          </div>
          ${this.structure ? this.renderStructure(this.structure) : 'Loading...'}
          <input type="file" @change=${this.handleUpload} multiple>
        </div>
      </div>
      <context-menu></context-menu>
    `;
  }
}

customElements.define('file-tree', FileTree);
