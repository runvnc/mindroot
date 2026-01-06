import { LitElement, html, css } from '/admin/static/js/lit-core.min.js';
import { BaseEl } from '/admin/static/js/base.js';

class EnvManager extends BaseEl {
  static properties = {
    pluginData: { type: Object },
    loading: { type: Boolean },
    editingVar: { type: String },
    newVarName: { type: String },
    newVarValue: { type: String },
    showAddForm: { type: Boolean },
    searchTerm: { type: String }
  };

  constructor() {
    super();
    this.pluginData = null;
    this.loading = true;
    this.editingVar = null;
    this.newVarName = '';
    this.newVarValue = '';
    this.showAddForm = false;
    this.searchTerm = '';
  }

  connectedCallback() {
    super.connectedCallback();
    this.fetchEnvVars();
  }

  async fetchEnvVars() {
    this.loading = true;
    try {
      const response = await fetch('/env_vars/scan');
      const result = await response.json();
      if (result.success) {
        this.pluginData = result.data;
      } else {
        console.error('Error fetching environment variables:', result.error);
      }
    } catch (error) {
      console.error('Error fetching environment variables:', error);
    } finally {
      this.loading = false;
    }
  }

  async updateEnvVar(varName, varValue) {
    try {
      const response = await fetch('/env_vars/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          var_name: varName,
          var_value: varValue
        })
      });

      const result = await response.json();
      if (result.success) {
        // Refresh the data
        await this.fetchEnvVars();
        return true;
      } else {
        console.error('Error updating environment variable:', result.message);
        return false;
      }
    } catch (error) {
      console.error('Error updating environment variable:', error);
      return false;
    }
  }

  handleEditClick(varName) {
    this.editingVar = varName;
  }

  async handleSaveEdit(varName) {
    const inputEl = this.shadowRoot.querySelector(`#edit-${varName}`);
    if (inputEl) {
      const newValue = inputEl.value;
      const success = await this.updateEnvVar(varName, newValue);
      if (success) {
        this.editingVar = null;
      }
    }
  }

  handleCancelEdit() {
    this.editingVar = null;
  }

  toggleAddForm() {
    this.showAddForm = !this.showAddForm;
    if (!this.showAddForm) {
      this.newVarName = '';
      this.newVarValue = '';
    }
  }

  async handleAddVar() {
    if (this.newVarName && this.newVarValue) {
      const success = await this.updateEnvVar(this.newVarName, this.newVarValue);
      if (success) {
        this.newVarName = '';
        this.newVarValue = '';
        this.showAddForm = false;
      }
    }
  }

  handleSearchInput(e) {
    this.searchTerm = e.target.value;
  }

  renderEnvironmentVars() {
    if (!this.pluginData || !this.pluginData.current_env) {
      return html`<div class="empty-state">No environment variables found</div>`;
    }

    const currentEnv = this.pluginData.current_env;
    
    // Create a mapping of variable names to the plugins that reference them
    const varsByPlugin = {};
    const pluginsByVar = {};
    
    for (const [pluginName, pluginInfo] of Object.entries(this.pluginData)) {
      if (pluginName === 'current_env') continue;
      
      for (const varName of pluginInfo.env_vars) {
        if (!varsByPlugin[pluginName]) {
          varsByPlugin[pluginName] = [];
        }
        varsByPlugin[pluginName].push(varName);
        
        if (!pluginsByVar[varName]) {
          pluginsByVar[varName] = [];
        }
        pluginsByVar[varName].push(pluginName);
      }
    }
    
    // Group variables by plugin
    const groupedByPlugin = {};
    const multiPluginVars = [];
    
    // First, identify variables referenced by multiple plugins
    for (const [varName, plugins] of Object.entries(pluginsByVar)) {
      if (plugins.length > 1) {
        multiPluginVars.push({
          varName,
          varValue: currentEnv[varName],
          plugins
        });
      } else {
        // Single plugin variables
        const plugin = plugins[0];
        if (!groupedByPlugin[plugin]) {
          groupedByPlugin[plugin] = [];
        }
        groupedByPlugin[plugin].push({
          varName,
          varValue: currentEnv[varName]
        });
      }
    }
    
    // Sort plugins alphabetically
    const sortedPlugins = Object.keys(groupedByPlugin).sort();
    
    // Sort multi-plugin variables by name
    multiPluginVars.sort((a, b) => a.varName.localeCompare(b.varName));
    
    // Apply search filter if needed
    let filteredPlugins = sortedPlugins;
    let filteredMultiVars = multiPluginVars;
    
    if (this.searchTerm) {
      const searchTerm = this.searchTerm.toLowerCase();
      
      // Filter plugins and their variables
      filteredPlugins = sortedPlugins.filter(plugin => {
        // Check if plugin name matches
        if (plugin.toLowerCase().includes(searchTerm)) return true;
        
        // Check if any variable name matches
        return groupedByPlugin[plugin].some(v => 
          v.varName.toLowerCase().includes(searchTerm) ||
          (v.varValue && v.varValue.toLowerCase().includes(searchTerm))
        );
      });
      
      // For each plugin, filter its variables
      for (const plugin of filteredPlugins) {
        groupedByPlugin[plugin] = groupedByPlugin[plugin].filter(v => 
          v.varName.toLowerCase().includes(searchTerm) ||
          plugin.toLowerCase().includes(searchTerm) ||
          (v.varValue && v.varValue.toLowerCase().includes(searchTerm))
        );
      }
      
      // Filter multi-plugin variables
      filteredMultiVars = multiPluginVars.filter(v => 
        v.varName.toLowerCase().includes(searchTerm) ||
        v.plugins.some(p => p.toLowerCase().includes(searchTerm)) ||
        (v.varValue && v.varValue.toLowerCase().includes(searchTerm))
      );
    }
    
    // Check if we have any results after filtering
    const hasResults = filteredPlugins.some(p => groupedByPlugin[p].length > 0) || filteredMultiVars.length > 0;
    
    if (!hasResults) {
      return html`<div class="empty-state">No matching environment variables found</div>`;
    }

    return html`
      <table class="env-table">
        <thead>
          <tr>
            <th>Variable Name</th>
            <th>Value</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${filteredPlugins.map(plugin => {
            if (groupedByPlugin[plugin].length === 0) return '';
            
            return html`
              <tr class="plugin-header">
                <td colspan="3" class="plugin-name">${plugin}</td>
              </tr>
              ${groupedByPlugin[plugin].map(v => {
                const { varName, varValue } = v;
                const isMasked = varValue === '********';
                
                return html`
                  <tr class="plugin-var">
                    <td><span class="var-name" title="${varName}">${varName}</span></td>
                    <td>
                      ${this.editingVar === varName ?
                        html`
                          <div class="edit-form">
                            <input 
                              id="edit-${varName}" 
                              type="text" 
                              value="${isMasked ? '' : varValue}" 
                              placeholder="${isMasked ? 'Enter new value' : ''}">
                          </div>
                        ` :
                        html`<span class="var-value ${isMasked ? 'masked' : ''}">${varValue}</span>`
                      }
                    </td>
                    <td>
                      <div class="actions">
                        ${this.editingVar === varName ?
                          html`
                            <button class="small primary" @click=${() => this.handleSaveEdit(varName)}>Save</button>
                            <button class="small" @click=${this.handleCancelEdit}>Cancel</button>
                          ` :
                          html`<button class="small" @click=${() => this.handleEditClick(varName)}>Edit</button>`
                        }
                      </div>
                    </td>
                  </tr>
                `;
              })}
            `;
          })}
          
          ${filteredMultiVars.length > 0 ? html`
            <tr class="plugin-header">
              <td colspan="3" class="plugin-name">Multiple Plugins</td>
            </tr>
            ${filteredMultiVars.map(v => {
              const { varName, varValue, plugins } = v;
              const isMasked = varValue === '********';
              
              return html`
                <tr class="plugin-var">
                  <td>
                    <span class="var-name" title="${varName}">${varName}</span>
                    <div class="plugin-refs">
                      ${plugins.map(p => html`<span class="plugin-tag">${p}</span>`)}
                    </div>
                  </td>
                  <td>
                    ${this.editingVar === varName ?
                      html`
                        <div class="edit-form">
                          <input 
                            id="edit-${varName}" 
                            type="text" 
                            value="${isMasked ? '' : varValue}" 
                            placeholder="${isMasked ? 'Enter new value' : ''}">
                        </div>
                      ` :
                      html`<span class="var-value ${isMasked ? 'masked' : ''}">${varValue}</span>`
                    }
                  </td>
                  <td>
                    <div class="actions">
                      ${this.editingVar === varName ?
                        html`
                          <button class="small primary" @click=${() => this.handleSaveEdit(varName)}>Save</button>
                          <button class="small" @click=${this.handleCancelEdit}>Cancel</button>
                        ` :
                        html`<button class="small" @click=${() => this.handleEditClick(varName)}>Edit</button>`
                      }
                    </div>
                  </td>
                </tr>
              `;
            })}
          ` : ''}
        </tbody>
      </table>
    `;
  }

  _render() {
    return html`
      <link rel="stylesheet" href="/env_manager/static/css/env-manager.css">
      <div class="env-manager">
        <div class="section">
          <h3>
            Environment Variables
            <div class="controls">
              <input 
                type="text" 
                class="search-box" 
                placeholder="Search..." 
                @input=${this.handleSearchInput} 
                .value=${this.searchTerm}>
              <button @click=${this.toggleAddForm}>
                ${this.showAddForm ? 'Cancel' : 'Add Variable'}
              </button>
            </div>
          </h3>

          ${this.loading ? 
            html`<div class="loading">Loading environment variables...</div>` :
            html`
              ${this.showAddForm ? 
                html`
                  <div class="add-form">
                    <div class="form-row">
                      <input 
                        type="text" 
                        placeholder="Variable Name" 
                        .value=${this.newVarName}
                        @input=${e => this.newVarName = e.target.value}>
                    </div>
                    <div class="form-row">
                      <input 
                        type="text" 
                        placeholder="Variable Value" 
                        .value=${this.newVarValue}
                        @input=${e => this.newVarValue = e.target.value}>
                    </div>
                    <div class="form-actions">
                      <button class="primary" @click=${this.handleAddVar}>Add Variable</button>
                    </div>
                  </div>
                ` : ''
              }

              ${this.renderEnvironmentVars()}
            `
          }
        </div>
      </div>
    `;
  }
}

customElements.define('env-manager', EnvManager);
