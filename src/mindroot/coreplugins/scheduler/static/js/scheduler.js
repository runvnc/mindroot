/**
 * Scheduler Manager Web Component
 * Provides UI for managing scheduled commands in MindRoot
 */

class SchedulerManager extends HTMLElement {
  constructor() {
    super();
    this.schedules = [];
    this.history = [];
    this.commands = [];
    this.activeTab = 'schedules';
    this.showCreateForm = false;
    this.loading = true;
  }

  connectedCallback() {
    this.render();
    this.loadData();
  }

  async loadData() {
    this.loading = true;
    this.render();

    try {
      const [schedulesRes, commandsRes] = await Promise.all([
        fetch('/scheduler/schedules'),
        fetch('/scheduler/commands')
      ]);

      if (schedulesRes.ok) {
        const data = await schedulesRes.json();
        this.schedules = data.schedules || [];
      }

      if (commandsRes.ok) {
        const data = await commandsRes.json();
        this.commands = data.commands || [];
      }
    } catch (error) {
      console.error('Error loading scheduler data:', error);
    }

    this.loading = false;
    this.render();
  }

  async loadHistory() {
    try {
      const res = await fetch('/scheduler/history?days=7');
      if (res.ok) {
        const data = await res.json();
        this.history = data.history || [];
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
    this.render();
  }

  async createSchedule(formData) {
    try {
      const res = await fetch('/scheduler/schedules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (res.ok) {
        this.showCreateForm = false;
        await this.loadData();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Failed to create schedule'}`);
      }
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Failed to create schedule');
    }
  }

  async pauseSchedule(scheduleId) {
    try {
      const res = await fetch(`/scheduler/schedules/${scheduleId}/pause`, {
        method: 'POST'
      });
      if (res.ok) {
        await this.loadData();
      }
    } catch (error) {
      console.error('Error pausing schedule:', error);
    }
  }

  async resumeSchedule(scheduleId) {
    try {
      const res = await fetch(`/scheduler/schedules/${scheduleId}/resume`, {
        method: 'POST'
      });
      if (res.ok) {
        await this.loadData();
      }
    } catch (error) {
      console.error('Error resuming schedule:', error);
    }
  }

  async deleteSchedule(scheduleId) {
    if (!confirm('Are you sure you want to delete this schedule?')) {
      return;
    }

    try {
      const res = await fetch(`/scheduler/schedules/${scheduleId}`, {
        method: 'DELETE'
      });
      if (res.ok) {
        await this.loadData();
      }
    } catch (error) {
      console.error('Error deleting schedule:', error);
    }
  }

  formatDate(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString();
  }

  formatRelativeTime(isoString) {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    const now = new Date();
    const diff = date - now;
    
    if (diff < 0) return 'Overdue';
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `in ${days}d ${hours % 24}h`;
    if (hours > 0) return `in ${hours}h ${minutes % 60}m`;
    return `in ${minutes}m`;
  }

  render() {
    this.innerHTML = `
      <div class="scheduler-container">
        <div class="scheduler-header">
          <h3>Scheduled Tasks</h3>
          <div class="scheduler-actions">
            <button class="btn btn-secondary" id="refresh-btn">
              <span class="material-icons">refresh</span>
              Refresh
            </button>
            <button class="btn btn-primary" id="create-btn">
              <span class="material-icons">add</span>
              New Schedule
            </button>
          </div>
        </div>

        <div class="scheduler-tabs">
          <button class="tab-btn ${this.activeTab === 'schedules' ? 'active' : ''}" data-tab="schedules">
            Schedules (${this.schedules.length})
          </button>
          <button class="tab-btn ${this.activeTab === 'history' ? 'active' : ''}" data-tab="history">
            History
          </button>
        </div>

        ${this.showCreateForm ? this.renderCreateForm() : ''}

        ${this.loading ? '<div class="loading">Loading</div>' : ''}

        ${!this.loading && this.activeTab === 'schedules' ? this.renderSchedules() : ''}
        ${!this.loading && this.activeTab === 'history' ? this.renderHistory() : ''}
      </div>
    `;

    this.attachEventListeners();
  }

  renderCreateForm() {
    const commandOptions = this.commands.map(cmd => 
      `<option value="${cmd.name}">${cmd.name}</option>`
    ).join('');

    return `
      <div class="create-schedule-form">
        <h4>Create New Schedule</h4>
        <form id="schedule-form">
          <div class="form-row">
            <div class="form-group">
              <label for="command">Command</label>
              <select id="command" name="command" required>
                <option value="">Select a command...</option>
                ${commandOptions}
              </select>
            </div>
            <div class="form-group">
              <label for="name">Name (optional)</label>
              <input type="text" id="name" name="name" placeholder="My scheduled task">
            </div>
          </div>

          <div class="form-group">
            <label for="schedule">Schedule</label>
            <input type="text" id="schedule" name="schedule" required
              placeholder="e.g., 'every day at 9:00', 'in 30 minutes', '0 8 * * *'">
            <small style="color: var(--text-muted); font-size: 0.75rem;">
              Supports: cron expressions, "in X minutes/hours", "every day at HH:MM", "tomorrow at HH:MM"
            </small>
          </div>

          <div class="form-group">
            <label for="args">Arguments (JSON, optional)</label>
            <textarea id="args" name="args" placeholder='{"key": "value"}'></textarea>
          </div>

          <div class="form-group">
            <label for="agent_name">Agent (optional)</label>
            <input type="text" id="agent_name" name="agent_name" placeholder="Agent name for context">
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" id="cancel-create">Cancel</button>
            <button type="submit" class="btn btn-primary">Create Schedule</button>
          </div>
        </form>
      </div>
    `;
  }

  renderSchedules() {
    if (this.schedules.length === 0) {
      return `
        <div class="empty-state">
          <span class="material-icons">schedule</span>
          <p>No scheduled tasks</p>
          <p>Click "New Schedule" to create one</p>
        </div>
      `;
    }

    return `
      <div class="schedule-list">
        ${this.schedules.map(schedule => this.renderScheduleItem(schedule)).join('')}
      </div>
    `;
  }

  renderScheduleItem(schedule) {
    const isPaused = !schedule.enabled;
    const statusClass = isPaused ? 'paused' : 'active';

    return `
      <div class="schedule-item ${statusClass}" data-id="${schedule.id}">
        <div class="schedule-item-header">
          <span class="schedule-name">${schedule.name || schedule.id}</span>
          <span class="schedule-status ${statusClass}">${statusClass}</span>
        </div>
        
        <div class="schedule-details">
          <div class="schedule-detail">
            <span class="schedule-detail-label">Command</span>
            <span class="schedule-detail-value">${schedule.command}</span>
          </div>
          <div class="schedule-detail">
            <span class="schedule-detail-label">Schedule</span>
            <span class="schedule-detail-value">${schedule.schedule_string || 'N/A'}</span>
          </div>
          <div class="schedule-detail">
            <span class="schedule-detail-label">Next Run</span>
            <span class="schedule-detail-value">${this.formatRelativeTime(schedule.next_run)}</span>
          </div>
          <div class="schedule-detail">
            <span class="schedule-detail-label">Last Run</span>
            <span class="schedule-detail-value">${this.formatDate(schedule.last_run)}</span>
          </div>
          <div class="schedule-detail">
            <span class="schedule-detail-label">Runs</span>
            <span class="schedule-detail-value">${schedule.run_count || 0} (${schedule.error_count || 0} errors)</span>
          </div>
        </div>

        <div class="schedule-actions">
          ${isPaused ? `
            <button class="btn btn-sm btn-secondary resume-btn" data-id="${schedule.id}">
              <span class="material-icons">play_arrow</span> Resume
            </button>
          ` : `
            <button class="btn btn-sm btn-secondary pause-btn" data-id="${schedule.id}">
              <span class="material-icons">pause</span> Pause
            </button>
          `}
          <button class="btn btn-sm btn-danger delete-btn" data-id="${schedule.id}">
            <span class="material-icons">delete</span> Delete
          </button>
        </div>
      </div>
    `;
  }

  renderHistory() {
    if (this.history.length === 0) {
      return `
        <div class="empty-state">
          <span class="material-icons">history</span>
          <p>No execution history</p>
        </div>
      `;
    }

    return `
      <div class="history-list">
        ${this.history.map(item => `
          <div class="history-item ${item.success ? 'success' : 'failed'}">
            <div class="history-header">
              <span class="history-command">${item.command} (${item.schedule_name})</span>
              <span class="history-time">${this.formatDate(item.executed_at)}</span>
            </div>
            ${item.error ? `<div class="history-error">${item.error}</div>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  attachEventListeners() {
    // Refresh button
    this.querySelector('#refresh-btn')?.addEventListener('click', () => {
      this.loadData();
    });

    // Create button
    this.querySelector('#create-btn')?.addEventListener('click', () => {
      this.showCreateForm = true;
      this.render();
    });

    // Cancel create
    this.querySelector('#cancel-create')?.addEventListener('click', () => {
      this.showCreateForm = false;
      this.render();
    });

    // Tab buttons
    this.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        this.activeTab = e.target.dataset.tab;
        if (this.activeTab === 'history' && this.history.length === 0) {
          this.loadHistory();
        } else {
          this.render();
        }
      });
    });

    // Create form
    this.querySelector('#schedule-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const formData = {
        command: form.command.value,
        schedule: form.schedule.value,
        name: form.name.value || null,
        agent_name: form.agent_name.value || null,
        args: null
      };

      // Parse args JSON if provided
      if (form.args.value.trim()) {
        try {
          formData.args = JSON.parse(form.args.value);
        } catch (err) {
          alert('Invalid JSON in arguments field');
          return;
        }
      }

      await this.createSchedule(formData);
    });

    // Pause buttons
    this.querySelectorAll('.pause-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.closest('.pause-btn').dataset.id;
        this.pauseSchedule(id);
      });
    });

    // Resume buttons
    this.querySelectorAll('.resume-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.closest('.resume-btn').dataset.id;
        this.resumeSchedule(id);
      });
    });

    // Delete buttons
    this.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.target.closest('.delete-btn').dataset.id;
        this.deleteSchedule(id);
      });
    });
  }
}

customElements.define('scheduler-manager', SchedulerManager);
