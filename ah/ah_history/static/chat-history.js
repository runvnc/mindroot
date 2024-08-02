import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class ChatHistory extends BaseEl {
  static properties = {
    user: { type: String },
    agent_name: { type: String },
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
    }
    file-:hover, sub-dir:hover {
     /* border: 1px solid #ccc; */
    }
    .selected-folder {
      background-color: rgba(0, 0, 255, 0.1);
    }
    .upload-container {
      margin-top: 10px;
    }
  `;

  constructor() {
    super();
    this.dir = '/';
 }

  async firstUpdated() {
    await this.loadStructure();
  }

  async loadStructure() {
    try {
      const response = await fetch(`/api/file-tree?dir=${encodeURIComponent(this.dir)}`);
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
          ?selected=${this.selectedFolder === item.path}
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

  _render() {
    return html`
      <div class="file-tree" @click=${this.handleOutsideClick}>
        <div class="tree-container">
          ${this.error ? html`<div class="error">${this.error}</div>` : ''}
          <div class="search-container">
            <input type="text" placeholder="Search files..." @input=${this.handleSearchInput}>
          </div>
          ${this.structure ? this.renderStructure(this.structure) : 'Loading...'}
        </div>
        <div class="upload-container">
          ${this.selectedFolder ? html`
            <p>Selected folder: ${this.selectedFolder}</p>
            <input type="file" @change=${this.handleUpload} multiple>
          ` : html`
            <p>Select a folder to enable upload</p>
          `}
        </div>
      </div>
      <context-menu></context-menu>
    `;
  }
}

customElements.define('chat-history', ChatHistory);
