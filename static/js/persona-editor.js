import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { BaseEl } from './base.js';
import './toggle-switch.js';

class PersonaEditor extends BaseEl {
  static properties = {
    persona: { type: Object },
    scope: { type: String },
    name: { type: String },
    personas: { type: Array },
    newPersona: { type: Boolean }
  };

  static styles = [
    css`
    `
  ];

  constructor() {
    super();
    this.persona = {};
    this.personas = [];
    this.scope = 'local';
    this.newPersona = false;
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
    //for (const key in this.persona) {
    //  formData.append(key, this.persona[key]);
    //}
    console.log('persona=', JSON.stringify(this.persona));
    formData.append('persona', this.persona)
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
    this.persona = { ...this.persona, [name]: files[0] };
  }

  _render() {
    return html`
      <div>
        <label>
          <input type="radio" name="scope" value="local" .checked=${this.scope === 'local'} @change=${this.handleScopeChange} /> Local
        </label>
        <label>
          <input type="radio" name="scope" value="shared" .checked=${this.scope === 'shared'} @change=${this.handleScopeChange} /> Shared
        </label>
        <select @change=${this.handlePersonaChange} .value=${this.name || ''} ?disabled=${this.newPersona}>
          <option value="">Select a persona</option>
          ${this.personas.map(persona => html`<option value="${persona.name}">${persona.name}</option>`) }
        </select>
        <button @click=${this.handleNewPersona}>New Persona</button>
      </div>
      <form @submit=${this.handleSubmit} class="persona">
        <label>
          Name:
          <input class="text_inp" type="text" name="name" .value=${this.persona.name || ''} @input=${this.handleInputChange} />
        </label>
        <label>
          Description:
          <textarea class="text_lg" name="description" .value=${this.persona.description || ''} @input=${this.handleInputChange}></textarea>
        </label>
        <label>
          Behavior:
          <textarea class="text_lg"  name="behavior" .value=${this.persona.behavior || ''} @input=${this.handleInputChange}></textarea>
        </label>
        <label>
          Speech Patterns:
          <textarea class="text_lg"  name="speech_patterns" .value=${this.persona.speech_patterns || ''} @input=${this.handleInputChange}></textarea>
        </label>
        <label>
          Appearance:
          <textarea  class="text_lg" name="appearance" .value=${this.persona.appearance || ''} @input=${this.handleInputChange}></textarea>
        </label>
        <label>
          Commands:
          <textarea  class="text_lg" name="commands" .value=${this.persona.commands || ''} @input=${this.handleInputChange}></textarea>
        </label>
        <label>
          Moderated:
          <toggle-switch .checked=${this.persona.moderated || false} @toggle-change=${(e) => this.handleInputChange({ target: { name: 'moderated', value: e.detail.checked, type: 'checkbox' } })}></toggle-switch>
        </label>
        <label>
          Face Reference Image:
          <input class="text_inp" type="file" name="faceref" @change=${this.handleFileChange} />
        </label>
        <label>
          Avatar Image:
          <input class="text_inp" type="file" name="avatar" @change=${this.handleFileChange} />
        </label>
        <button  class="btn" type="submit">Save</button>
      </form>
    `;
  }
}

customElements.define('persona-editor', PersonaEditor);
