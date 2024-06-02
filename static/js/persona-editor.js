import { LitElement, html, css } from '/static/js/lit-core.min.js';
import { BaseEl } from './base.js';

class PersonaEditor extends BaseEl {
  static properties = {
    persona: { type: Object },
    scope: { type: String },
    name: { type: String }
  };

  static styles = css`
    form {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      max-width: 600px;
      margin: auto;
    }
    label {
      display: flex;
      flex-direction: column;
      font-weight: bold;
    }
  `;

  constructor() {
    super();
    this.persona = {};
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchPersona();
  }

  async fetchPersona() {
    const response = await fetch(`/personas/${this.scope}/${this.name}`);
    this.persona = await response.json();
  }

  handleInputChange(event) {
    const { name, value } = event.target;
    this.persona = { ...this.persona, [name]: value };
  }

  async handleSubmit(event) {
    event.preventDefault();
    const response = await fetch(`/personas/${this.scope}/${this.name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.persona)
    });
    if (response.ok) {
      alert('Persona updated successfully');
    } else {
      alert('Failed to update persona');
    }
  }

  render() {
    return html`
      <form @submit=${this.handleSubmit}>
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
        <button  class="btn" type="submit">Save</button>
      </form>
    `;
  }
}

customElements.define('persona-editor', PersonaEditor);
