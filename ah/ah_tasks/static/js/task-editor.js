import { LitElement, html, css } from '../../lit-core.min.js';

class TaskEditor extends LitElement {
  static properties = {
    tasks: { type: Array },
    currentTask: { type: Object },
  };

  static styles = css`
    :host {
      display: block;
      padding: 16px;
      color: var(--color-text);
    }
    .task-list {
      margin-bottom: 16px;
    }
    .task-form {
      display: grid;
      gap: 16px;
    }
    .admin-files {
      margin-top: 16px;
    }
    .admin-file {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .file-upload {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  `;

  constructor() {
    super();
    this.tasks = [];
    this.currentTask = null;
    this.loadTasks();
  }

  async loadTasks() {
    const response = await fetch('/tasks');
    this.tasks = await response.json();
  }

  async loadTask(name) {
    const response = await fetch(`/tasks/${name}`);
    this.currentTask = await response.json();
  }

  async saveTask() {
    const method = this.currentTask.id ? 'PUT' : 'POST';
    const url = this.currentTask.id ? `/tasks/${this.currentTask.name}` : '/tasks';
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(this.currentTask),
    });
    if (response.ok) {
      this.loadTasks();
    } else {
      console.error('Failed to save task');
    }
  }

  async deleteTask(name) {
    const response = await fetch(`/tasks/${name}`, { method: 'DELETE' });
    if (response.ok) {
      this.loadTasks();
      this.currentTask = null;
    } else {
      console.error('Failed to delete task');
    }
  }

  async uploadAdminFile(event) {
    const file = event.target.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_description', 'Admin uploaded file');

    const response = await fetch(`/tasks/${this.currentTask.name}/admin-files`, {
      method: 'POST',
      body: formData,
    });

    if (response.ok) {
      this.loadTask(this.currentTask.name);
    } else {
      console.error('Failed to upload admin file');
    }
  }

  async deleteAdminFile(fileName) {
    const response = await fetch(`/tasks/${this.currentTask.name}/admin-files/${fileName}`, {
      method: 'DELETE',
    });

    if (response.ok) {
      this.loadTask(this.currentTask.name);
    } else {
      console.error('Failed to delete admin file');
    }
  }

  render() {
    return html`
      <div class="task-list">
        <h2>Tasks</h2>
        <ul>
          ${this.tasks.map(task => html`
            <li>
              <button @click=${() => this.loadTask(task.name)}>${task.name}</button>
              <button @click=${() => this.deleteTask(task.name)}>Delete</button>
            </li>
          `)}
        </ul>
        <button @click=${() => this.currentTask = { name: '', description: '', user_input_fields: [], admin_input_files: [], output_schema: {} }}>New Task</button>
      </div>

      ${this.currentTask ? html`
        <div class="task-form">
          <h2>${this.currentTask.id ? 'Edit' : 'New'} Task</h2>
          <input placeholder="Task Name" .value=${this.currentTask.name} @input=${e => this.currentTask.name = e.target.value}>
          <textarea placeholder="Description" .value=${this.currentTask.description} @input=${e => this.currentTask.description = e.target.value}></textarea>
          
          <h3>User Input Fields</h3>
          ${this.currentTask.user_input_fields.map((field, index) => html`
            <div>
              <input placeholder="Field Name" .value=${field.name} @input=${e => this.currentTask.user_input_fields[index].name = e.target.value}>
              <select .value=${field.type} @change=${e => this.currentTask.user_input_fields[index].type = e.target.value}>
                <option value="text">Text</option>
                <option value="number">Number</option>
                <option value="file">File</option>
              </select>
              ${field.type === 'file' ? html`
                <input placeholder="Allowed Extensions" .value=${field.allowed_extensions.join(', ')} @input=${e => this.currentTask.user_input_fields[index].allowed_extensions = e.target.value.split(', ')}>
              ` : ''}
              <button @click=${() => this.currentTask.user_input_fields.splice(index, 1)}>Remove</button>
            </div>
          `)}
          <button @click=${() => this.currentTask.user_input_fields.push({ name: '', type: 'text' })}>Add Field</button>

          <h3>Admin Input Files</h3>
          <div class="admin-files">
            ${this.currentTask.admin_input_files.map(file => html`
              <div class="admin-file">
                <span>${file.name}</span>
                <button @click=${() => this.deleteAdminFile(file.name)}>Delete</button>
              </div>
            `)}
            <div class="file-upload">
              <input type="file" @change=${this.uploadAdminFile}>
              <button @click=${() => this.shadowRoot.querySelector('input[type=file]').click()}>Upload File</button>
            </div>
          </div>

          <h3>Output Schema</h3>
          <textarea placeholder="Output Schema (JSON)" .value=${JSON.stringify(this.currentTask.output_schema, null, 2)} @input=${e => this.currentTask.output_schema = JSON.parse(e.target.value)}></textarea>

          <button @click=${this.saveTask}>Save Task</button>
        </div>
      ` : ''}
    `;
  }
}

customElements.define('task-editor', TaskEditor);
