import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class ChecklistHelp extends BaseEl {
  static properties = {
    expanded: { type: Boolean }
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
      color: var(--text-color);
    }

    .checklist-help {
      display: flex;
      flex-direction: column;
      width: 100%;
      max-width: 1200px;
      margin: 0 auto;
      gap: 20px;
    }

    .section {
      background: rgb(10, 10, 25);
      border-radius: 8px;
      padding: 1rem;
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    h3 {
      margin-top: 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 0.5rem;
    }

    h4 {
      margin-top: 1.5rem;
      margin-bottom: 0.5rem;
    }

    pre {
      background: rgba(0, 0, 0, 0.2);
      padding: 1rem;
      border-radius: 4px;
      overflow-x: auto;
      font-family: monospace;
      white-space: pre-wrap;
    }

    code {
      font-family: monospace;
      background: rgba(0, 0, 0, 0.2);
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
    }

    .example-button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.5rem 1rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-top: 1rem;
    }

    .example-button:hover {
      background: #3a3a50;
    }

    .copy-button {
      background: #2a2a40;
      color: #fff;
      border: 1px solid rgba(255, 255, 255, 0.1);
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.2s;
      margin-left: 0.5rem;
      font-size: 0.8rem;
    }

    .copy-button:hover {
      background: #3a3a50;
    }

    .code-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.5rem;
    }

    .setup-steps {
      margin-top: 1rem;
      padding-left: 1.5rem;
    }

    .setup-steps li {
      margin-bottom: 0.5rem;
    }

    .advanced-section {
      margin-top: 2rem;
      border-top: 1px solid rgba(255, 255, 255, 0.1);
      padding-top: 1rem;
    }

    .command-table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
    }

    .command-table th,
    .command-table td {
      text-align: left;
      padding: 0.5rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .command-table th {
      background: rgba(0, 0, 0, 0.2);
    }

    .warning {
      background: rgba(255, 100, 0, 0.1);
      border-left: 4px solid rgba(255, 100, 0, 0.7);
      padding: 0.75rem 1rem;
      margin: 1rem 0;
      border-radius: 0 4px 4px 0;
    }
  `;

  constructor() {
    super();
    this.expanded = false;
  }

  toggleExpanded() {
    this.expanded = !this.expanded;
  }

  copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  }

  _render() {
    const exampleChecklist = `## Checklist

- [ ] First task

    This is the description for the first task.
    It can span multiple lines.

- [ ] Second task

    Description for the second task.
    With more details.

- [ ] Final task

    Complete this last task.`;

    const advancedExample = `## Checklist

- [ ] Setup environment

    Install required dependencies and configure settings.

- [ ] Data collection

    Gather all necessary data from the specified sources.

- [ ] Data analysis

    Analyze the collected data using appropriate methods.
    If analysis reveals issues, goto "Setup environment" to reconfigure.

- [ ] Generate report

    Create a comprehensive report based on the analysis.
    If more data is needed, goto "Data collection".

- [ ] Present findings

    Present the final report and findings to stakeholders.`;

    return html`
      <div class="checklist-help">
        <div class="section">
          <h3>Checklist Plugin</h3>
          <p>
            The Checklist plugin helps agents work through a sequence of tasks defined in Markdown format.
            It parses task lists from the agent instructions and provides commands to track progress.
            When the agent marks a task as complete, it receives a reminder of the instructions for the next task.
            This should help it focus on instructions for each subtask so it is less likely to miss important details.
          </p>
          
          <h4>How to Format a Checklist</h4>
          <p>Add a checklist section to your agent instructions using this format (must start with heading "Checklist"):</p>
          
          <div class="code-header">
            <span>Example Checklist Format:</span>
            <button class="copy-button" @click=${() => this.copyToClipboard(exampleChecklist)}>Copy</button>
          </div>
          <pre>${exampleChecklist}</pre>
          
          <div class="warning">
            <strong>Important:</strong> Do not use Markdown headings (lines starting with #) inside subtask descriptions. 
            Headings will be interpreted as an end to the checklist! Keep all subtask content as plain text or 
            use other Markdown formatting like lists, bold, or italic text.
          </div>
          
          <h4>Setup Instructions</h4>
          <ol class="setup-steps">
            <li>Enable the checklist commands for your agent under <b>Agent Settings</b> → <b>Available Commands</b> → <b>checklist</b></li>
            <li>Add a checklist section to your agent instructions using the format shown above. <strong> Remember to start your checklist with a heading named "Checklist"!</strong></li>
            <li>The agent will automatically parse the checklist and track progress</li>
          </ol>
          
          <h4>Basic Usage</h4>
          <p>The agent can complete tasks using:</p>
          <pre>{ "complete_subtask": {} }  # Complete current subtask</pre>
          
          <p>When a task is completed, the agent will receive a summary of the completed task and the next task to work on.</p>
          
          <div class="advanced-section">
            <h4>Advanced Features</h4>
            <p>The checklist plugin supports non-linear workflows with these additional commands:</p>
            
            <table class="command-table">
              <tr>
                <th>Command</th>
                <th>Description</th>
                <th>Example</th>
              </tr>
              <tr>
                <td><code>complete_subtask</code></td>
                <td>Complete a specific subtask by number or label</td>
                <td><code>{ "complete_subtask": { "subtask_id": "Data analysis" } }</code></td>
              </tr>
              <tr>
                <td><code>goto_subtask</code></td>
                <td>Navigate to a specific subtask without changing its status</td>
                <td><code>{ "goto_subtask": { "subtask_id": 3 } }</code></td>
              </tr>
              <tr>
                <td><code>clear_subtask</code></td>
                <td>Mark a subtask as incomplete</td>
                <td><code>{ "clear_subtask": { "subtask_id": "Setup environment" } }</code></td>
              </tr>
              <tr>
                <td><code>get_checklist_status</code></td>
                <td>Show the current status of all subtasks</td>
                <td><code>{ "get_checklist_status": {} }</code></td>
              </tr>
            </table>
            
            <h4>Non-Linear Workflow Example</h4>
            <p>Here's an example of a checklist designed for non-linear navigation:</p>
            
            <div class="code-header">
              <span>Advanced Checklist Example:</span>
              <button class="copy-button" @click=${() => this.copyToClipboard(advancedExample)}>Copy</button>
            </div>
            <pre>${advancedExample}</pre>
            
            <p>With this checklist, the agent can navigate between tasks as needed based on conditions or user requests.</p>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('checklist-help', ChecklistHelp);
