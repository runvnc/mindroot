import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class IndexList extends BaseEl {
  static properties = {
    indices: { type: Array },
    selectedIndex: { type: Object },
    loading: { type: Boolean }
  }

  static styles = css`
    :host {
      flex: 0 0 300px;
      border-right: 1px solid rgba(255, 255, 255, 0.1);
      padding-right: 15px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .create-index {
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      background: #2196F3;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 6px;
      color: white;
      cursor: pointer;
      font-size: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      transition: background-color 0.2s;
    }

    .create-index:hover {
      background: #1976D2;
    }

    .index-entries {
      overflow-y: auto;
      flex-grow: 1;
    }

    .index-entry {
      padding: 10px;
      margin: 5px 0;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
      background: rgba(255, 255, 255, 0.05);
    }

    .index-entry:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .index-entry.selected {
      background: #2196F3;
      border-color: #1976D2;
      color: white;
    }

    .index-entries::-webkit-scrollbar {
      width: 8px;
    }

    .index-entries::-webkit-scrollbar-track {
      background: rgba(10, 10, 25, 0.95);
    }

    .index-entries::-webkit-scrollbar-thumb {
      background-color: #333;
      border-radius: 10px;
      border: 2px solid rgba(10, 10, 25, 0.95);
    }

    .index-entries::-webkit-scrollbar-thumb:hover {
      background-color: #444;
    }
  `;

  async createNewIndex() {
    const name = prompt('Enter name for new index:');
    if (!name) return;

    try {
      const response = await fetch('/index/create-index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: '',
          version: '1.0.0'
        })
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('index-created', {
          detail: result.data
        }));
      } else {
        alert(`Failed to create index: ${result.message}`);
      }
    } catch (error) {
      console.error('Error creating index:', error);
      alert('Failed to create index');
    }
  }

  handleIndexClick(index) {
    this.dispatchEvent(new CustomEvent('index-selected', {
      detail: index
    }));
  }

  _render() {
    return html`
      <button class="create-index" @click=${this.createNewIndex}
              ?disabled=${this.loading}>
        <span class="material-icons">add</span>
        Create New Index
      </button>
      <div class="index-entries">
        ${this.indices.map(index => html`
          <div class="index-entry ${this.selectedIndex?.name === index.name ? 'selected' : ''}"
               @click=${() => this.handleIndexClick(index)}>
            ${index.name}
          </div>
        `)}
      </div>
    `;
  }
}

customElements.define('index-list', IndexList);
