import { html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';

export class SubDir extends BaseEl {
  static properties = {
    dir: { type: String },
    path: { type: String },
    collapsed: { type: Boolean }
  };

  static styles = css`
    .sub-dir {
      margin-left: 20px;
    }
    .dir-name {
      cursor: pointer;
      padding: 5px;
    }
    .dir-name:hover {
      background-color: rgba(0, 0, 0, 0.1);
    }
  `;

  constructor() {
    super();
    this.dir = '';
    this.path = '';
    this.collapsed = false;
  }

  firstUpdated() {
    this.addEventListener('contextmenu', this.handleContextMenu);
  }

  _render() {
    return html`
      <div class="sub-dir">
        <div class="dir-name" @click=${this.toggleCollapse}>
          ${this.collapsed ? '▶' : '▼'} ${this.dir}
        </div>
        ${this.collapsed ? '' : html`<slot></slot>`}
      </div>
    `;
  }

  toggleCollapse() {
    this.collapsed = !this.collapsed;
    this.dispatch('dir-toggled', { dir: this.dir, path: this.path, collapsed: this.collapsed });
  }

  handleContextMenu(e) {
    e.preventDefault();
    const fileTree = document.querySelector('file-tree');
    if (!fileTree) {
      console.error('file-tree element not found');
      return;
    }
    const contextMenu = fileTree.getEl('context-menu');
    if (!contextMenu) {
      console.error('context-menu element not found');
      return;
    }
    const menuItems = [{ label: 'Create Dir', action: () => this.createNewFolder() }];
    contextMenu.show(e.clientX, e.clientY, menuItems);
  }

  async createNewFolder() {
    const folderName = prompt('Enter the new folder name:');
    if (folderName) {
      const newFolderPath = `${this.path}/${folderName}`;
      console.log('Creating new folder:', newFolderPath);
      
      try {
        const response = await fetch('/api/create_folder', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: `path=${encodeURIComponent(newFolderPath)}`,
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Folder created successfully:', result);
        
        // Dispatch event to update the file tree
        this.dispatch('new-folder-created', { path: newFolderPath });
      } catch (error) {
        console.error('Error creating folder:', error);
        alert('Failed to create folder. Please try again.');
      }
    }
  }
}

customElements.define('sub-dir', SubDir);
