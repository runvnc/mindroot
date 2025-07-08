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
    alert('__TRANSLATE_checklist_copied_alert__');
  }

  _render() {
    const exampleChecklist = `## __TRANSLATE_checklist_example_heading__

- [ ] __TRANSLATE_checklist_example_first_task__

    __TRANSLATE_checklist_example_first_desc__
    __TRANSLATE_checklist_example_multiline__

- [ ] __TRANSLATE_checklist_example_second_task__

    __TRANSLATE_checklist_example_second_desc__
    __TRANSLATE_checklist_example_more_details__

- [ ] __TRANSLATE_checklist_example_final_task__

    __TRANSLATE_checklist_example_final_desc__`;

    const advancedExample = `## __TRANSLATE_checklist_example_heading__

- [ ] __TRANSLATE_checklist_advanced_setup__

    __TRANSLATE_checklist_advanced_setup_desc__

- [ ] __TRANSLATE_checklist_advanced_data_collection__

    __TRANSLATE_checklist_advanced_data_collection_desc__

- [ ] __TRANSLATE_checklist_advanced_data_analysis__

    __TRANSLATE_checklist_advanced_data_analysis_desc__
    __TRANSLATE_checklist_advanced_analysis_condition__

- [ ] __TRANSLATE_checklist_advanced_generate_report__

    __TRANSLATE_checklist_advanced_generate_report_desc__
    __TRANSLATE_checklist_advanced_report_condition__

- [ ] __TRANSLATE_checklist_advanced_present_findings__

    __TRANSLATE_checklist_advanced_present_findings_desc__`;

    return html`
      <div class="checklist-help">
        <div class="section">
          <h3>__TRANSLATE_checklist_title__</h3>
          <p>
            __TRANSLATE_checklist_description__
          </p>
          
          <h4>__TRANSLATE_checklist_format_heading__</h4>
          <p>__TRANSLATE_checklist_format_instruction__</p>
          
          <div class="code-header">
            <span>__TRANSLATE_checklist_example_format_label__</span>
            <button class="copy-button" @click=${() => this.copyToClipboard(exampleChecklist)}>__TRANSLATE_checklist_copy_button__</button>
          </div>
          <pre>${exampleChecklist}</pre>
          
          <div class="warning">
            <strong>__TRANSLATE_checklist_warning_title__</strong> __TRANSLATE_checklist_warning_text__
          </div>
          
          <h4>__TRANSLATE_checklist_setup_heading__</h4>
          <ol class="setup-steps">
            <li>__TRANSLATE_checklist_setup_step1__</li>
            <li>__TRANSLATE_checklist_setup_step2__</li>
            <li>__TRANSLATE_checklist_setup_step3__</li>
          </ol>
          
          <h4>__TRANSLATE_checklist_basic_usage_heading__</h4>
          <p>__TRANSLATE_checklist_basic_usage_text__</p>
          <pre>{ "complete_subtask": {} }  # __TRANSLATE_checklist_complete_current_comment__</pre>
          
          <p>__TRANSLATE_checklist_completion_description__</p>
          
          <div class="advanced-section">
            <h4>__TRANSLATE_checklist_advanced_heading__</h4>
            <p>__TRANSLATE_checklist_advanced_description__</p>
            
            <table class="command-table">
              <tr>
                <th>__TRANSLATE_checklist_table_command__</th>
                <th>__TRANSLATE_checklist_table_description__</th>
                <th>__TRANSLATE_checklist_table_example__</th>
              </tr>
              <tr>
                <td><code>complete_subtask</code></td>
                <td>__TRANSLATE_checklist_cmd_complete_desc__</td>
                <td><code>{ "complete_subtask": { "subtask_id": "__TRANSLATE_checklist_cmd_example_data_analysis__" } }</code></td>
              </tr>
              <tr>
                <td><code>goto_subtask</code></td>
                <td>__TRANSLATE_checklist_cmd_goto_desc__</td>
                <td><code>{ "goto_subtask": { "subtask_id": 3 } }</code></td>
              </tr>
              <tr>
                <td><code>clear_subtask</code></td>
                <td>__TRANSLATE_checklist_cmd_clear_desc__</td>
                <td><code>{ "clear_subtask": { "subtask_id": "__TRANSLATE_checklist_cmd_example_setup__" } }</code></td>
              </tr>
              <tr>
                <td><code>get_checklist_status</code></td>
                <td>__TRANSLATE_checklist_cmd_status_desc__</td>
                <td><code>{ "get_checklist_status": {} }</code></td>
              </tr>
            </table>
            
            <h4>__TRANSLATE_checklist_nonlinear_heading__</h4>
            <p>__TRANSLATE_checklist_nonlinear_description__</p>
            
            <div class="code-header">
              <span>__TRANSLATE_checklist_advanced_example_label__</span>
              <button class="copy-button" @click=${() => this.copyToClipboard(advancedExample)}>__TRANSLATE_checklist_copy_button__</button>
            </div>
            <pre>${advancedExample}</pre>
            
            <p>__TRANSLATE_checklist_nonlinear_conclusion__</p>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('checklist-help', ChecklistHelp);
