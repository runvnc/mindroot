import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class SubscriptionTemplates extends BaseEl {
  static properties = {
    templates: { type: Array },
    loading: { type: Boolean },
    showNewTemplateForm: { type: Boolean },
    editingTemplate: { type: Object }
  }

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }

    .header-actions {
      display: flex;
      justify-content: flex-end;
      margin-bottom: 1rem;
    }

    .templates-list {
      margin-bottom: 2rem;
    }
    
    .template-card {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .template-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }
    
    .template-name {
      font-size: 1.1rem;
      font-weight: 500;
    }
    
    .template-description {
      margin-bottom: 0.5rem;
      color: rgba(255, 255, 255, 0.7);
    }
    
    .template-preview {
      margin-top: 0.5rem;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border-radius: 4px;
      font-family: monospace;
      font-size: 0.9rem;
      max-height: 100px;
      overflow-y: auto;
    }
    
    .default-badge {
      display: inline-block;
      padding: 0.25rem 0.5rem;
      background: #4a5af8;
      color: white;
      border-radius: 4px;
      font-size: 0.8rem;
      margin-left: 0.5rem;
    }

    .new-template-form {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
      margin-bottom: 1rem;
    }
    
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 1rem;
    }
    
    .form-group {
      margin-bottom: 1rem;
    }
    
    .form-label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }
    
    .form-control {
      width: 100%;
      padding: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 4px;
      color: white;
    }
    
    .form-actions {
      display: flex;
      justify-content: flex-end;
      gap: 1rem;
    }
    
    .btn {
      padding: 0.5rem 1rem;
      border-radius: 4px;
      border: none;
      cursor: pointer;
      font-weight: 500;
    }
    
    .btn-primary {
      background: #4a5af8;
      color: white;
    }
    
    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: white;
    }
    
    .btn-danger {
      background: #f85a5a;
      color: white;
    }
    
    .btn-sm {
      padding: 0.25rem 0.5rem;
      font-size: 0.8rem;
    }
  `;

  constructor() {
    super();
    this.templates = [];
    this.loading = false;
    this.showNewTemplateForm = false;
    this.editingTemplate = null;
  }

  toggleNewTemplateForm() {
    this.showNewTemplateForm = !this.showNewTemplateForm;
    this.editingTemplate = null;
  }

  editTemplate(template) {
    this.editingTemplate = {...template};
    this.showNewTemplateForm = true;
  }

  async handleSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const templateData = {};
    
    for (const [key, value] of formData.entries()) {
      templateData[key] = value;
    }
    
    try {
      let response;
      let result;
      
      if (this.editingTemplate) {
        // Update existing template
        response = await fetch(`/admin/subscriptions/templates/${this.editingTemplate.template_id}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(templateData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Template updated successfully!');
          this.dispatchEvent(new CustomEvent('template-updated', {
            detail: result.template,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to update template: ' + (result.message || 'Unknown error'));
        }
      } else {
        // Create new template
        response = await fetch('/admin/subscriptions/templates', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(templateData)
        });
        
        result = await response.json();
        
        if (result.status === 'success') {
          alert('Template created successfully!');
          this.dispatchEvent(new CustomEvent('template-created', {
            detail: result.template,
            bubbles: true,
            composed: true
          }));
        } else {
          alert('Failed to create template: ' + (result.message || 'Unknown error'));
        }
      }
      
      // Reset form and state
      this.showNewTemplateForm = false;
      this.editingTemplate = null;
      form.reset();
      
    } catch (error) {
      alert('Error saving template: ' + error.message);
    }
  }

  async setDefaultTemplate(templateId) {
    try {
      const response = await fetch(`/admin/subscriptions/templates/${templateId}/set-default`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        alert('Template set as default successfully!');
        this.dispatchEvent(new CustomEvent('template-updated', {
          bubbles: true,
          composed: true
        }));
      } else {
        alert('Failed to set template as default: ' + (result.message || 'Unknown error'));
      }
    } catch (error) {
      alert('Error setting template as default: ' + error.message);
    }
  }

  render() {
    return html`
      <div>
        <div class="header-actions">
          <button class="btn btn-primary" @click=${this.toggleNewTemplateForm}>
            ${this.showNewTemplateForm ? 'Cancel' : 'New Template'}
          </button>
        </div>

        ${this.showNewTemplateForm ? html`
          <div class="new-template-form">
            <h3>${this.editingTemplate ? 'Edit Template' : 'Create New Template'}</h3>
            <form @submit=${this.handleSubmit}>
              <div class="form-grid">
                <div class="form-group">
                  <label class="form-label" for="template_name">Template Name</label>
                  <input type="text" class="form-control" id="template_name" name="name" 
                         value=${this.editingTemplate?.name || ''} required>
                </div>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="template_description">Description</label>
                <textarea class="form-control" id="template_description" name="description" rows="2" required>
                  ${this.editingTemplate?.description || ''}
                </textarea>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="html_template">HTML Template</label>
                <textarea class="form-control" id="html_template" name="html_template" rows="10" required>
                  ${this.editingTemplate?.html_template || ''}
                </textarea>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="css_template">CSS Template</label>
                <textarea class="form-control" id="css_template" name="css_template" rows="6" required>
                  ${this.editingTemplate?.css_template || ''}
                </textarea>
              </div>
              
              <div class="form-group">
                <label class="form-label" for="js_template">JavaScript Template</label>
                <textarea class="form-control" id="js_template" name="js_template" rows="6" required>
                  ${this.editingTemplate?.js_template || ''}
                </textarea>
              </div>
              
              <div class="form-actions">
                <button type="button" class="btn btn-secondary" @click=${this.toggleNewTemplateForm}>
                  Cancel
                </button>
                
                <button type="submit" class="btn btn-primary">
                  ${this.editingTemplate ? 'Update Template' : 'Create Template'}
                </button>
              </div>
            </form>
          </div>
        ` : ''}

        <div class="templates-list">
          ${this.loading ? html`<p>Loading templates...</p>` : ''}
          
          ${!this.loading && this.templates.length === 0 ? html`<p>No templates defined yet.</p>` : ''}
          
          ${this.templates.map(template => html`
            <div class="template-card">
              <div class="template-header">
                <div class="template-name">
                  ${template.name}
                  ${template.is_default ? html`<span class="default-badge">Default</span>` : ''}
                </div>
              </div>
              
              <div class="template-description">${template.description}</div>
              
              <div class="template-preview">
                ${template.html_template.substring(0, 100)}...
              </div>
              
              <div class="plan-actions" style="margin-top: 0.5rem;">
                <button class="btn btn-secondary btn-sm" @click=${() => this.editTemplate(template)}>
                  Edit
                </button>
                
                ${!template.is_default ? html`
                  <button class="btn btn-primary btn-sm" @click=${() => this.setDefaultTemplate(template.template_id)}>
                    Set as Default
                  </button>
                ` : ''}
              </div>
            </div>
          `)}
        </div>
      </div>
    `;
  }
}

customElements.define('subscription-templates', SubscriptionTemplates);
