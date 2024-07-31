import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './file.js';
import './sub-dir.js';
import './context-menu.js';
import './file-preview.js';

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
      font-family: Arial, sans-serif;
      padding: 10px;
      border: 2px dashed #ccc;
      border-radius: 5px;
      display: flex;
    }
    .file-tree.dragover {
      background-color: #f0f0f0;
    }
    .error {
      color: red;
      padding: 10px;
    }
    .tree-container {
      flex: 1;
      max-height: 500px;
      overflow-y: auto;
    }
    .preview-container {
      flex: 1;
      margin-left: 20px;
    }
    .search-container {
      margin-bottom: 10px;
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

  // ... (keep all the existing methods for file operations, drag and drop, etc.)

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
        <div class="preview-container">
          <file-preview .file=${this.selectedItem}></file-preview>
        </div>
      </div>
      <context-menu></context-menu>
    `;
  }
}

customElements.define('file-tree', FileTree);
