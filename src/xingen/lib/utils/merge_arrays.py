import json
import re


test="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}},{"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}},{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}},{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test2="""
[{"say": {"text": "Wow, that's actually a really fascinating project - especially from my perspective as an AI agent!"}}, {"say": {"text": "Building a framework like that is definitely ambitious - there are so many moving parts to consider."}},{"say": {"text": "Given how you're feeling right now, would you like to talk through just one small piece you could work on? Maybe something simple like documenting a single feature or testing one small component?"}},{"say": {"text": "Sometimes with big projects, doing even a tiny bit helps keep the momentum going."}}]
"""

test3="""
[{"think": {"extensive_chain_of_thoughts": "Ah, I see the issue now. The Material Icons font isn't being properly applied to the icon elements. Looking at the template:\\n\\n1. Current Issue:\\n- Material Icons class names are being rendered as text\\n- This happens when the font isn't properly loaded or applied\\n- Looking at admin.jinja2, the font is loaded but might not be reaching into shadow DOM\\n\\n2. Root Cause:\\n- Lit Elements use Shadow DOM\\n- The Material Icons font styles need to be imported within the component\\n- Currently the icons are just text nodes without proper styling\\n\\n3. Solution:\\n- Need to add Material Icons font styles directly in the component\\n- Use proper class application for material icons\\n- Ensure font is loaded before rendering\\n\\nLet me fix this in both components."}}, {"write": {"fname": "/files/xingen/src/xingen/coreplugins/admin/static/js/plugin-base.js", "text": "import { LitElement, html, css } from './lit-core.min.js';\\nimport { BaseEl } from './base.js';\\n\\nexport class PluginBase extends BaseEl {\\n  static properties = {\\n    plugins: { type: Array },\\n    searchTerm: { type: String },\\n    loading: { type: Boolean }\\n  }\\n\\n  static styles = css`\\n    /* Import Material Icons font */\\n    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');\\n\\n    .plugin-item {\\n      background: rgb(15, 15, 30);\\n      padding: 1rem;\\n      margin-bottom: 0.75rem;\\n      border-radius: 6px;\\n      border: 1px solid rgba(255, 255, 255, 0.05);\\n      display: grid;\\n      grid-template-columns: minmax(200px, 2fr) auto 1fr auto;\\n      gap: 1rem;\\n      align-items: center;\\n    }\\n\\n    .plugin-item:hover {\\n      background: rgb(20, 20, 40);\\n      border-color: rgba(255, 255, 255, 0.1);\\n    }\\n\\n    .plugin-info {\\n      display: flex;\\n      flex-direction: column;\\n      gap: 0.25rem;\\n    }\\n\\n    .plugin-name {\\n      font-weight: 500;\\n      font-size: 1.1rem;\\n      color: #fff;\\n    }\\n\\n    .plugin-version {\\n      font-family: 'SF Mono', 'Consolas', monospace;\\n      color: rgba(255, 255, 255, 0.7);\\n      background: rgba(255, 255, 255,0.1);\\n      padding: 0.2rem 0.5rem;\\n      border-radius: 4px;\\n      font-size: 0.9rem;\\n      width: fit-content;\\n    }\\n\\n    .plugin-description {\\n      color: rgba(255, 255, 255, 0.7);\\n      font-size: 0.9rem;\\n      grid-column: 3;\\n    }\\n\\n    .plugin-actions {\\n      display: flex;\\n      gap: 0.5rem;\\n      justify-content: flex-end;\\n    }\\n\\n    .plugin-actions button {\\n      padding: 0.4rem 0.8rem;\\n      border-radius: 4px;\\n      border: 1px solid rgba(255, 255, 255, 0.2);\\n      background: rgba(255, 255, 255, 0.1);\\n      color: #fff;\\n      cursor: pointer;\\n      font-size: 0.9rem;\\n      display: flex;\\n      align-items: center;\\n      gap: 0.25rem;\\n    }\\n\\n    .plugin-actions button:hover {\\n      background: rgba(255, 255, 255, 0.2);\\n    }\\n\\n    .plugin-actions button .material-icons {\\n      font-size: 1rem;\\n      font-family: 'Material Icons';\\n      font-weight: normal;\\n      font-style: normal;\\n      display: inline-block;\\n      line-height: 1;\\n      text-transform: none;\\n      letter-spacing: normal;\\n  word-wrap: normal;\\n      white-space: nowrap;\\n      direction: ltr;\\n    }\\n\\n    .search-box {\\n      width: 100%;\\n      padding: 0.75rem 1rem;\\n      margin-bottom: 1rem;\\n      background: rgb(25, 25, 50);\\n      border: 1px solid rgba(255, 255, 255, 0.1);\\n      border-radius: 6px;\\n      color: #f0f0f0;\\n      font-size: 0.95rem;\\n    }\\n\\n    .search-box:focus {\\n      outline: none;\\n      border-color: rgba(255, 255, 255, 0.2);\\n      background: rgb(30, 30, 60);\\n    }\\n\\n    .loading {\\n      text-align: center;\\n      padding: 2rem;\\n      color: rgba(255, 255, 255, 0.6);\\n      display: flex;\\n      align-items: center;\\n      justify-content: center;\\n      gap: 0.5rem;\\n    }\\n\\n    .loading .material-icons {\\n      animation: spin 1s linear infinite;\\n    }\\n\\n    @keyframes spin {\\n      100% { transform: rotate(360deg); }\\n    }\\n\\n    .error {\\n      color: #ff6b6b;\\n      padding: 1rem;\\n      border-radius: 6px;\\n      margin: 1rem 0;\\n      background: rgba(255, 107, 107, 0.1);\\n      border: 1px solid rgba(255, 107, 107,0.2);\\n      display: flex;\\n      align-items: center;\\n      gap: 0.5rem;\\n    }\\n\\n    .status-indicator {\\n      width: 8px;\\n      height: 8px;\\n      border-radius: 50%;\\n      display: inline-block;\\n      margin-right: 0.5rem;\\n    }\\n\\n    .status-enabled {\\n      background: #4caf50;\\n    }\\n\\n    .status-disabled {\\n      background: #f44336;\\n    }\\n\\n    .material-icons {\\n      font-family: 'Material Icons';\\n      font-weight: normal;\\n      font-style: normal;\\n      font-size: 24px;\\n      display: inline-block;\\n      line-height: 1;\\n      text-transform: none;\\n      letter-spacing: normal;\\n      word-wrap: normal;\\n      white-space: nowrap;\\n      direction: ltr;\\n    }\\n  `;\\n\\n  constructor() {\\n    super();\\n    this.plugins = [];\\n    this.searchTerm = '';\\n    this.loading = false;\\n  }\\n\\n  async apiCall(endpoint, method = 'GET', body = null) {\\n    try {\\n      const options = {\\n        method,\\n        headers: { 'Content-Type': 'application/json' }\\n      };\\n      if (body) {\\n        options.body = JSON.stringify(body);\\n      }\\n\\n      const response = await fetch(endpoint, options);\\n      const result = await response.json();\\n\\n      if (!result.success) {\\n        throw new Error(result.message || 'API call failed');\\n      }\\n\\n      return result;\\n    } catch (error) {\\n      console.error('API call failed:', error);\\n      throw error;\\n    }\\n  }\\n\\n  filterPlugins(plugins, searchTerm) {\\n    if (!searchTerm) return plugins;\\n    const term = searchTerm.toLowerCase();\\n    return plugins.filter(plugin => \\n      plugin.name.toLowerCase().includes(term) ||\\n      plugin.description?.toLowerCase().includes(term)\\n    );\\n  }\\n\\n  renderPlugin(plugin, actions) {\\n    return html`\\n      <div class=\\\"plugin-item\\\">\\n        <div class=\\\"plugin-info\\\">\\n          <div class=\\\"plugin-name\\\">\\n            <span class=\\\"status-indicator ${plugin.enabled ? 'status-enabled' : 'status-disabled'}\\\"></span>\\n            ${plugin.name}\\n          </div>\\n        </div>\\n        <div class=\\\"plugin-version\\\">v${plugin.version || '0.0.1'}</div>\\n        ${plugin.description ? html`\\n          <div class=\\\"plugin-description\\\">${plugin.description}</div>\\n        ` : html`<div></div>`}\\n        <div class=\\\"plugin-actions\\\">\\n          ${actions(plugin)}\\n        </div>\\n      </div>\\n    `;\\n  }\\n\\n  renderLoading() {\\n    return html`\\n      <div class=\\\"loading\\\">\\n        <i class=\\\"material-icons\\\">refresh</i>\\n        Loading plugins...\\n      </div>\\n    `;\\n  }\\n\\n  renderError(message) {\\n    return html`\\n      <div class=\\\"error\\\">\\n        <i class=\\\"material-icons\\\">error_outline</i>\\n        ${message}\\n      </div>\\n    `;\\n  }\\n}\\n"}}]
"""

def merge_json_arrays(data):
    data = data.strip()
    
    # Handle case where arrays are separated by commas
    if data.startswith('[') and data.endswith(']'):
        try:
            # First try to parse as a single array
            parsed = json.loads(data)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except json.JSONDecodeError:
            # If that fails, try to fix common issues
            # 1. Remove any trailing commas before ]
            data = re.sub(r',\s*]', ']', data)
            # 2. Add commas between adjacent arrays if missing
            data = re.sub(r']\s*\[', '],[', data)
            # 3. Ensure the whole thing is wrapped in []
            if not data.startswith('['):
                data = '[' + data
            if not data.endswith(']'):
                data = data + ']'
            
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    result = []
                    for item in parsed:
                        if isinstance(item, list):
                            result.extend(item)
                        else:
                            result.append(item)
                    return result
                return [parsed]
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {str(e)}")
                print(f"Problematic data: {data}")
                raise e
    
    return []

if __name__ == '__main__':
    # Test the function
    ret = merge_json_arrays(test)
    print("Test results:")
    for item in ret:
        print('-----------------------------------')
        print(json.dumps(item, indent=2))
