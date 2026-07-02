import { LitElement, html, css } from '/chat/static/js/lit-core.min.js';
import { BaseEl } from '/chat/static/js/base.js';

/**
 * ChecklistWidget - renders a nice visual checklist in the chat UI.
 *
 * Registered command handlers intercept results from:
 *   complete_subtask, goto_subtask, clear_subtask,
 *   get_checklist_status, create_checklist
 *
 * The Python commands return markdown strings.  We parse the
 * "### Checklist Status" section (and the leading action line) to
 * build a structured representation, then render it as a widget
 * with a progress bar, checkboxes, and nested subtask indentation.
 */

/* ------------------------------------------------------------------ */
/*  Markdown -> structured parser                                      */
/* ------------------------------------------------------------------ */

function parseChecklistMarkdown(md) {
  if (!md || typeof md !== 'string') return null;

  const result = {
    action: '',       // e.g. "Completed Subtask 1: ..."
    nextTask: null,   // { label, body }
    allComplete: false,
    title: '',
    tasks: [],
  };

  const lines = md.split('\n');

  // Extract action line(s) before the status section
  const statusIdx = lines.findIndex(l => l.trim().startsWith('### Checklist Status'));
  if (statusIdx === -1) {
    // No status section - might be an error or simple message
    result.action = md.trim();
    return result;
  }

  // Everything before the status section is the action / next-task info
  const preStatus = lines.slice(0, statusIdx);
  const preLines = [];
  for (const line of preStatus) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith('All subtasks complete')) {
      result.allComplete = true;
      continue;
    }
    if (trimmed.startsWith('Next subtask')) {
      // Next subtask header line - the following lines are the task body
      continue;
    }
    if (trimmed.startsWith('- [ ]') || trimmed.startsWith('- [x]') || trimmed.startsWith('- [X]')) {
      // This is the next task label
      const label = trimmed.replace(/^-\s*\[[ xX]\]\s*/, '');
      result.nextTask = { label, body: '' };
      continue;
    }
    if (result.nextTask) {
      // Body line for the next task
      if (result.nextTask.body) result.nextTask.body += '\n';
      result.nextTask.body += line;
    } else {
      preLines.push(trimmed);
    }
  }
  result.action = preLines.join('\n');

  // Parse the status section
  const statusLines = lines.slice(statusIdx + 1);
  let currentTask = null;

  for (const line of statusLines) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    // Top-level task line: starts with emoji + **Subtask**:
    // Patterns: "➡️ **Subtask**: Label"  or  "✅ **Subtask**: Label"  or  "❌ **Subtask**: Label"
    const topMatch = trimmed.match(/^(\S+(?:\ufe0f)?)\s*\*\*Subtask\*\*:\s*(.+)$/);
    if (topMatch) {
      const statusEmoji = topMatch[1];
      const label = topMatch[2];
      const isCurrent = statusEmoji.includes('\u27a1'); // ➡
      const isDone = statusEmoji.includes('\u2705');    // ✅
      currentTask = {
        label,
        done: isDone,
        current: isCurrent,
        nested: [],
      };
      result.tasks.push(currentTask);
      continue;
    }

    // Nested task line: "  ✅ Label" or "  ❌ Label"
    const nestedMatch = trimmed.match(/^(\u2705|\u274c)\s+(.+)$/);
    if (nestedMatch && currentTask) {
      const isDone = nestedMatch[1] === '\u2705';
      currentTask.nested.push({
        label: nestedMatch[2],
        done: isDone,
      });
      continue;
    }
  }

  return result;
}

/* ------------------------------------------------------------------ */
/*  Widget element                                                     */
/* ------------------------------------------------------------------ */

class ChecklistWidget extends BaseEl {
  static properties = {
    data: { type: Object },
  };

  static styles = css`
    :host {
      display: block;
      width: 100%;
    }
    .checklist-widget {
      background: var(--checklist-bg, rgba(20, 20, 35, 0.6));
      border: 1px solid var(--checklist-border, rgba(255, 255, 255, 0.08));
      border-radius: 10px;
      padding: 14px 16px;
      margin: 8px 0;
      font-family: system-ui, -apple-system, sans-serif;
      color: var(--text-color, #e0e0e0);
    }
    .cw-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .cw-title {
      font-size: 0.95em;
      font-weight: 600;
      color: var(--checklist-title, #c8c8e0);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .cw-progress-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.8em;
      color: var(--checklist-progress-text, #888);
    }
    .cw-progress-bar {
      width: 100px;
      height: 6px;
      background: rgba(255, 255, 255, 0.08);
      border-radius: 3px;
      overflow: hidden;
    }
    .cw-progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #4a9eff, #6ec1ff);
      border-radius: 3px;
      transition: width 0.4s ease;
    }
    .cw-action {
      font-size: 0.82em;
      color: var(--checklist-action, #8a9aff);
      margin-bottom: 8px;
      padding: 4px 8px;
      background: rgba(74, 158, 255, 0.08);
      border-radius: 4px;
      border-left: 3px solid #4a9eff;
    }
    .cw-next-task {
      font-size: 0.82em;
      color: var(--checklist-next, #aaa);
      margin-bottom: 8px;
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.03);
      border-radius: 4px;
    }
    .cw-next-task .label {
      font-weight: 600;
      color: var(--checklist-next-label, #c0c0d0);
    }
    .cw-next-task .body {
      margin-top: 4px;
      font-size: 0.9em;
      color: var(--checklist-next-body, #888);
      white-space: pre-wrap;
    }
    .cw-tasks {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .cw-task {
      display: flex;
      align-items: flex-start;
      padding: 5px 6px;
      border-radius: 5px;
      transition: background 0.15s;
    }
    .cw-task:hover {
      background: rgba(255, 255, 255, 0.03);
    }
    .cw-task.current {
      background: rgba(74, 158, 255, 0.1);
      border-left: 3px solid #4a9eff;
      padding-left: 8px;
    }
    .cw-checkbox {
      width: 18px;
      height: 18px;
      border-radius: 4px;
      border: 2px solid var(--checklist-box, #555);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-right: 8px;
      margin-top: 1px;
      font-size: 11px;
      transition: all 0.2s;
    }
    .cw-checkbox.done {
      background: #4a9eff;
      border-color: #4a9eff;
      color: #fff;
    }
    .cw-checkbox.current {
      border-color: #4a9eff;
      background: rgba(74, 158, 255, 0.15);
    }
    .cw-task-label {
      font-size: 0.88em;
      line-height: 1.4;
    }
    .cw-task.done .cw-task-label {
      text-decoration: line-through;
      color: var(--checklist-done-text, #666);
    }
    .cw-task.current .cw-task-label {
      color: var(--checklist-current-text, #c8d8ff);
      font-weight: 500;
    }
    .cw-nested {
      list-style: none;
      padding: 0;
      margin: 2px 0 2px 26px;
    }
    .cw-nested .cw-task {
      padding: 3px 4px;
    }
    .cw-nested .cw-checkbox {
      width: 14px;
      height: 14px;
      font-size: 9px;
      margin-right: 6px;
    }
    .cw-nested .cw-task-label {
      font-size: 0.82em;
      color: var(--checklist-nested-text, #999);
    }
    .cw-all-done {
      text-align: center;
      padding: 10px;
      color: #4aff88;
      font-weight: 600;
      font-size: 0.9em;
    }
    .cw-empty {
      color: var(--checklist-empty, #666);
      font-style: italic;
      font-size: 0.85em;
      padding: 8px;
    }
  `;

  constructor() {
    super();
    this.data = null;
  }

  connectedCallback() {
    super.connectedCallback();
    // Parse data from attribute if not already set as property
    if (!this.data) {
      const raw = this.getAttribute('data');
      if (raw) {
        try {
          // Data is base64-encoded JSON to avoid HTML attribute escaping issues
          this.data = JSON.parse(atob(raw));
        } catch (e) {
          console.error('[checklist-widget] Failed to parse data attribute:', e);
        }
      }
    }
  }

  _render() {
    if (!this.data) {
      return html`<div class="checklist-widget"><div class="cw-empty">No checklist data</div></div>`;
    }

    const d = this.data;
    const total = d.tasks.length;
    const doneCount = d.tasks.filter(t => t.done).length;
    const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;

    return html`
      <div class="checklist-widget">
        <div class="cw-header">
          <div class="cw-title">
            <span>\u{1F4DD}</span> Checklist
          </div>
          ${total > 0 ? html`
            <div class="cw-progress-wrap">
              <span>${doneCount}/${total}</span>
              <div class="cw-progress-bar">
                <div class="cw-progress-fill" style="width: ${pct}%"></div>
              </div>
              <span>${pct}%</span>
            </div>
          ` : ''}
        </div>

        ${d.action ? html`<div class="cw-action">${d.action}</div>` : ''}

        ${d.nextTask ? html`
          <div class="cw-next-task">
            <div class="label">\u27a1\ufe0f Next: ${d.nextTask.label}</div>
            ${d.nextTask.body && d.nextTask.body.trim() ? html`<div class="body">${d.nextTask.body.trim()}</div>` : ''}
          </div>
        ` : ''}

        ${d.allComplete ? html`<div class="cw-all-done">\u2705 All subtasks complete!</div>` : ''}

        ${d.tasks.length > 0 ? html`
          <ul class="cw-tasks">
            ${d.tasks.map(task => html`
              <li class="cw-task ${task.done ? 'done' : ''} ${task.current ? 'current' : ''}">
                <div class="cw-checkbox ${task.done ? 'done' : ''} ${task.current ? 'current' : ''}">
                  ${task.done ? '\u2713' : (task.current ? '\u27a1' : '')}
                </div>
                <div>
                  <div class="cw-task-label">${task.label}</div>
                  ${task.nested && task.nested.length > 0 ? html`
                    <ul class="cw-nested">
                      ${task.nested.map(nested => html`
                        <li class="cw-task ${nested.done ? 'done' : ''}">
                          <div class="cw-checkbox ${nested.done ? 'done' : ''}">
                            ${nested.done ? '\u2713' : ''}
                          </div>
                          <div class="cw-task-label">${nested.label}</div>
                        </li>
                      `)}
                    </ul>
                  ` : ''}
                </div>
              </li>
            `)}
          </ul>
        ` : html`<div class="cw-empty">No tasks found</div>`}
      </div>
    `;
  }
}

customElements.define('checklist-widget', ChecklistWidget);

/* ------------------------------------------------------------------ */
/*  Command handler registration                                       */
/* ------------------------------------------------------------------ */

const CHECKLIST_COMMANDS = [
  'complete_subtask',
  'goto_subtask',
  'clear_subtask',
  'get_checklist_status',
  'create_checklist',
  'get_parsed_subtasks',
  'delegate_subtask',
];

/**
 * Build widget HTML string to inject into chat message content.
 * Returns an HTML string containing a <checklist-widget> element
 * with the parsed data serialized as a JSON attribute.
 */
function buildWidgetHtml(md) {
  const parsed = parseChecklistMarkdown(md);
  if (!parsed) return '';
  // Base64-encode the JSON to avoid HTML attribute escaping issues
  // (single quotes, double quotes, angle brackets in task labels, etc.)
  const b64 = btoa(JSON.stringify(parsed));
  return `<checklist-widget data="${b64}"></checklist-widget>`;
}

function handleChecklistCommand(data) {
  // Determine the markdown source depending on event type
  let md = null;
  if (data.event === 'result') {
    md = data.result;
  } else if (data.event === 'partial') {
    md = data.params?.markdown || data.params?.text || data.args?.markdown || data.args?.text;
  } else if (data.event === 'running') {
    md = data.args?.markdown || data.args?.text;
  }

  if (!md || typeof md !== 'string') {
    return null;
  }

  // Only render widget if we can parse a checklist status from the markdown
  const parsed = parseChecklistMarkdown(md);
  if (!parsed || (parsed.tasks.length === 0 && !parsed.allComplete && !parsed.action)) {
    return null;
  }

  return buildWidgetHtml(md);
}

// Register handlers for all checklist commands
for (const cmd of CHECKLIST_COMMANDS) {
  window.registerCommandHandler(cmd, (data) => {
    console.log(`[checklist-widget] handler for ${cmd}`, data);
    return handleChecklistCommand(data);
  });
}

console.log('[checklist-widget] Registered checklist command handlers:', CHECKLIST_COMMANDS);
