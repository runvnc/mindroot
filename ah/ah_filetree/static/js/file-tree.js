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
      /* background-color: blue; rgba(200, 200, 200, 0.1); */
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
    this.addEventListener('contextmenu', this.handleContextMenu);
    document.addEventListener('click', () => this.getEl('context-menu').hide());
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
      return html`<file- name=${item.name} path=${item.path} @file-selected=${this.handleFileSelected}></file->`;
    } else if (item.type === 'directory') {
      return html`
        <sub-dir dir=${item.name} path=${item.path} ?collapsed=${item.collapsed} @dir-toggled=${this.handleDirToggled}>
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

  handleContextMenu(e) {
    e.preventDefault();
    const contextMenu = this.getEl('context-menu');
    contextMenu.show(e.clientX, e.clientY, this.selectedItem);
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
