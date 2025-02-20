import { LitElement, html, css } from './lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class PersonaEditor extends BaseEl {
  static properties = {
    persona: { type: Object },
    scope: { type: String, reflect: true },
    name: { type: String, reflect: true },
    personas: { type: Array, reflect: true },
    newPersona: { type: Boolean, reflect: true },
    facerefFileName: { type: String, reflect: true },
    avatarFileName: { type: String, reflect: true }
  };

  static styles = [
    css`
      :host {
        display: block;
        margin-top: 20px;
      }

      .persona-editor {
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.02);
      }

      .persona-selector {
        display: flex;
        gap: 10px;
        align-items: center;
        margin-bottom: 20px;
      }

      .scope-selector {
        display: flex;
        gap: 15px;
        align-items: center;
        padding: 8px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
      }

      .scope-selector label {
        display: flex;
        align-items: center;
        gap: 5px;
        color: #f0f0f0;
        cursor: pointer;
      }

      select {
        flex: 1;
        padding: 8px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 4px;
        color: #f0f0f0;
      }

      .form-group {
        margin-bottom: 15px;
      }

      .form-group label {
        display: block;
        margin-bottom: 5px;
        color: #f0f0f0;
        font-weight: 500;
      }

      .file-upload-container {
        margin-bottom: 15px;
        padding: 12px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 6px;
      }

      .file-upload-label {
        display: block;
        margin-bottom: 8px;
        color: #f0f0f0;
        font-weight: 500;
      }

      .file-name {
        display: block;
        margin-top: 8px;
        color: #4a9eff;
        font-size: 0.9em;
      }

      .btn {
        padding: 8px 16px;
        background: #4a9eff;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .btn:hover {
        background: #3d8ae0;
      }

      .btn-secondary {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #f0f0f0;
      }

      .btn-secondary:hover {
        background: rgba(255, 255, 255, 0.15);
      }
    `
  ];

  constructor() {
    super();
    this.attachShadow({mode: 'open'});
    this.persona = {};
    this.personas = [];
    this.scope = 'local';
    this.newPersona = false;
    this.facerefFileName = '';
    this.avatarFileName = '';
    this.fetchPersonas();
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchPersona();
  }

  async fetchPersonas() {
    const response = await fetch(`/personas/${this.scope}`);
    this.personas = await response.json();
  }

  async fetchPersona() {
    if (!this.newPersona && this.name) {
      const response = await fetch(`/personas/${this.scope}/${this.name}`);
      this.persona = await response.json();
    } else {
      this.persona = {};
    }
  }

  handleScopeChange(event) {
    this.scope = event.target.value;
    this.fetchPersonas();
  }

  handlePersonaChange(event) {
    this.name = event.target.value;
    this.newPersona = false;
    this.fetchPersona();
  }

  handleNewPersona() {
    this.newPersona = true;
    this.persona = {};
    this.facerefFileName = '';
    this.avatarFileName = '';
  }

  handleInputChange(event) {
    const { name, value, type, checked } = event.target;
    const inputValue = type === 'checkbox' ? checked : value;
    this.persona = { ...this.persona, [name]: inputValue };
  }

  async handleSubmit(event) {
    event.preventDefault();
    const method = this.newPersona ? 'POST' : 'PUT';
    const url = this.newPersona ? `/personas/${this.scope}` : `/personas/${this.scope}/${this.name}`;
    const formData = new FormData();
    console.log('persona=', JSON.stringify(this.persona));
    formData.append('persona', JSON.stringify(this.persona))
    const faceref = this.shadowRoot.querySelector('input[name="faceref"]').files[0];
    const avatar = this.shadowRoot.querySelector('input[name="avatar"]').files[0];
    if (faceref) formData.append('faceref', faceref);
    if (avatar) formData.append('avatar', avatar);
    const response = await fetch(url, {
      method,
      body: formData
    });
    if (response.ok) {
      alert('Persona saved successfully');
      this.newPersona = false;
      this.fetchPersonas();
    } else {
      alert('Failed to save persona');
    }
  }

  handleFileChange(event) {
    const { name, files } = event.target;
    if (files.length > 0) {
      this.persona = { ...this.persona, [name]: files[0] };
      if (name === 'faceref') {
        this.facerefFileName = files[0].name;
      } else if (name === 'avatar') {
        this.avatarFileName = files[0].name;
      }
    }
  }

  _render() {
    return html`
      <div class="persona-editor">
        <div class="persona-selector">
          <div class="scope-selector">
            <label>
              <input type="radio" name="scope" value="local" .checked=${this.scope === 'local'} @change=${this.handleScopeChange} /> Local
            </label>
            <label>
              <input type="radio" name="scope" value="shared" .checked=${this.scope === 'shared'} @change=${this.handleScopeChange} /> Shared
            </label>
          </div>
          <select @change=${this.handlePersonaChange} .value=${this.name || ''} ?disabled=${this.newPersona}>
            <option value="">Select a persona</option>
            ${this.personas.map(persona => html`<option value="${persona.name}">${persona.name}</option>`) }
          </select>
          <button class="btn btn-secondary" @click=${this.handleNewPersona}>New Persona</button>
        </div>
        <form @submit=${this.handleSubmit} class="persona">
          <div class="form-group">
            <label>Name:</label>
            <input class="text_inp" type="text" name="name" .value=${this.persona.name || ''} @input=${this.handleInputChange} />
          </div>
          <div class="form-group">
            <label>Description:</label>
            <textarea class="text_lg" name="description" .value=${this.persona.description || ''} @input=${this.handleInputChange}></textarea>
          </div>
          <div class="form-group">
            <label>Speech Patterns:</label>
            <textarea class="text_lg" name="speech_patterns" .value=${this.persona.speech_patterns || ''} @input=${this.handleInputChange}></textarea>
          </div>
          <div class="form-group">
            <label>Appearance:</label>
            <textarea class="text_lg" name="appearance" .value=${this.persona.appearance || ''} @input=${this.handleInputChange}></textarea>
          </div>
          <div class="form-group">
            <label>Negative Appearance:</label>
            <textarea class="text_lg" name="negative_appearance" .value=${this.persona.negative_appearance || ''} @input=${this.handleInputChange}></textarea>
          </div>
          <div class="form-group">
        <label>
          Moderated:
          <toggle-switch .checked=${this.persona.moderated || false} @toggle-change=${(e) => this.handleInputChange({ target: { name: 'moderated', value: e.detail.checked, type: 'checkbox' } })}></toggle-switch>
        </label>
          </div>
        <div class="file-upload-container">
          <label class="file-upload-label" for="faceref">Choose Face Reference Image</label>
          <input id="faceref" type="file" name="faceref" @change=${this.handleFileChange} />
          <span class="file-name">${this.facerefFileName}</span>
        </div>
        <div class="file-upload-container">
          <label class="file-upload-label" for="avatar">Choose Avatar Image</label>
          <input id="avatar" type="file" name="avatar" @change=${this.handleFileChange} />
          <span class="file-name">${this.avatarFileName}</span>
        </div>
        <button class="btn" type="submit" id="save-persona">Save Persona</button>
      </form>
      </div>
    `;
  }
}

customElements.define('persona-editor', PersonaEditor);
