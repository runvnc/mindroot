import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class IndexMetadata extends BaseEl {
  static properties = {
    selectedIndex: { type: Object },
    loading: { type: Boolean }
  }

  static styles = css`
    :host {
      display: block;
      margin-bottom: 20px;
    }

    .index-metadata input {
      width: 100%;
      padding: 10px;
      margin: 5px 0;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 6px;
      color: #f0f0f0;
      font-size: 0.95rem;
    }

    .index-metadata input:focus {
      outline: none;
      border-color: rgba(255, 255, 255, 0.2);
      background: rgba(255, 255, 255, 0.08);
    }

    .index-metadata input:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
  `;

  async handleInputChange(e) {
    const field = e.target.name;
    const value = e.target.value;

    try {
      const response = await fetch(`/index/update-index/${this.selectedIndex.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: this.selectedIndex.name,
          description: this.selectedIndex.description,
          version: this.selectedIndex.version,
          [field]: value
        })
      });

      const result = await response.json();
      if (result.success) {
        this.dispatchEvent(new CustomEvent('metadata-updated', {
          detail: { field, value }
        }));
      } else {
        alert(`Failed to update index: ${result.message}`);
      }
    } catch (error) {
      console.error('Error updating index:', error);
      alert('Failed to update index');
    }
  }

  _render() {
    if (!this.selectedIndex) return html``;

    return html`
      <div class="index-metadata">
        <input type="text" name="name" 
               value=${this.selectedIndex.name}
               @change=${this.handleInputChange}
               ?disabled=${this.loading}
               placeholder="Index Name">
        <input type="text" name="description"
               value=${this.selectedIndex.description || ''}
               @change=${this.handleInputChange}
               ?disabled=${this.loading}
               placeholder="Description">
        <input type="text" name="version"
               value=${this.selectedIndex.version || '1.0.0'}
               @change=${this.handleInputChange}
               ?disabled=${this.loading}
               placeholder="Version">
      </div>
    `;
  }
}

customElements.define('index-metadata', IndexMetadata);
