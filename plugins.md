# MindRoot Plugin System

## Overview
The MindRoot plugin system is a modular architecture that combines Python backend functionality with web components for the frontend. It provides a flexible way to extend the system's capabilities through commands, services, and web UI components.

## Plugin Structure

For frontend component details, see below.

plugin_name/
├── src/
│   └── plugin_name/
│       ├── templates/       # Main page templates
│       ├── static/         # Static assets (auto-mounted if directory exists)
│       ├── inject/         # Templates to inject into existing blocks
│       ├── override/       # Templates to replace existing blocks
│       ├── mod.py          # Commands and services
│       ├── router.py       # FastAPI routes (auto-mounted if present)
│       └── __init__.py     # Plugin initialization
├── plugin_info.json       # Plugin metadata and configuration
├── pyproject.toml        # Build system requirements
├── setup.py             # Package installation
└── README.md           # Documentation
```

## Key Components

### 1. Plugin Configuration (plugin_info.json)
```json
{
  "name": "Plugin Name",
  "version": "1.0.0",
  "description": "Plugin description",
  "services": ["service_name"],
  "commands": ["command_name"]
}
```

### 2. Plugin Initialization (__init__.py)
```python
# This import is currently required for the plugin to load properly
# Will be improved in future versions
from .mod import *
```

### 3. Backend (Python)

#### Command Registration
```python
from lib.providers.commands import command

@command()
async def my_command(params, context=None):
    """Command implementation"""
    pass
```

#### Service Registration
```python
from lib.providers.services import service

@service()
async def my_service(params, context=None):
    """Service implementation"""
    pass
```

#### Route Handlers (Optional)
```python
# router.py - will be automatically mounted if present
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from lib.templates import render

router = APIRouter()

@router.get("/endpoint")
async def handler(request: Request):
    # Templates must be in templates/[page_name].jinja2
    user = request.state.user.username
    html = await render('page_name', {"context": "data", "user": user })
    return HTMLResponse(html)
```

### 4. Template System

The main chat template (mindroot/coreplugins/chat/templates/chat.jinja2) provides these blocks for plugin customization:

#### Head Section Blocks
```jinja2
{% block head_meta %}      {# Meta tags, charset, viewport #}
{% block title %}          {# Page title #}
{% block head_styles %}    {# CSS includes (must include <link> or <style> tag) #}
{% block head_scripts %}   {# JavaScript includes (must include <script> tags ) #}
{% block head_favicon %}   {# Favicon definitions #}
{% block head_extra %}     {# Additional head content #}
```

#### Body Section Blocks
```jinja2
{% block body_init %}      {# Initial JavaScript setup #}
{% block pre_content %}    {# Left sidebar content #}
{% block insert %}         {# Additional content area #}
{% block content %}        {# Main chat interface #}
{% block body_extra %}     {# Additional body content #}
```

#### Template Injection Example
```jinja2
{# inject/chat.jinja2 - Simple button injection example #}
{% block pre_content %}
    <div class="my-plugin-section">
        <a href="/my-plugin/action">
            <button class="plugin-btn">Plugin Action</button>
        </a>
    </div>
{% endblock %}
```

#### Template Override Example
```jinja2
{# override/chat.jinja2 - Will replace entire pre_content block #}

{% block pre_content %}
    <div class="custom-sidebar">
        <h2>Custom Sidebar</h2>
        <nav>
            <ul>
                <li><a href="#">Menu Item 1</a></li>
                <li><a href="#">Menu Item 2</a></li>
            </ul>
        </nav>
    </div>
{% endblock %}
```

# Frontend Integration Guide

The chat system is built on web components using the Lit library. The source code is available in the [mindroot repository](https://github.com/runvnc/mindroot).

### Key Source Files

- [base.js](https://github.com/runvnc/mindroot/blob/main/src/mindroot/coreplugins/chat/static/js/base.js) - Base component with theme support
- [chat.js](https://github.com/runvnc/mindroot/blob/main/src/mindroot/coreplugins/chat/static/js/chat.js) - Main chat component and SSE handling
- [action.js](https://github.com/runvnc/mindroot/blob/main/src/mindroot/coreplugins/chat/static/js/action.js) - Command result display
- [chatmessage.js](https://github.com/runvnc/mindroot/blob/main/src/mindroot/coreplugins/chat/static/js/chatmessage.js) - Message component
- [chatform.js](https://github.com/runvnc/mindroot/blob/main/src/mindroot/coreplugins/chat/static/js/chatform.js) - Input handling

### Base Component Class

All custom components should extend the `BaseEl` class. The BaseEl class provides:

- Automatic theme handling (`this.theme`)
- Convenient DOM querying (`this.getEl(selector)`)
- Custom event dispatch helper (`this.dispatch(name, detail)`)
- Automatic style injection through the render method

Example component:

```javascript
import { BaseEl } from '/chat/static/js/base.js';

class MyComponent extends BaseEl {
  static properties = {
    // Your component properties
  };

  constructor() {
    super();
    // Your initialization
  }

  // Override _render instead of render
  _render() {
    return html`
      <div>Your component content</div>
    `;
  }
}
```

### Command Handler System

The chat system uses a global registry for command handlers. Handlers receive events with different phases:

- 'partial' - Incremental updates during command execution
- 'running' - Command is actively executing
- 'result' - Final command result

Example command handler:

```javascript
window.registerCommandHandler('my_command', (data) => {
  console.log('Handler for', data.command);
  
  switch(data.event) {
    case 'partial':
      // Handle incremental updates
      return handlePartial(data.params);
    
    case 'running':
      // Show progress indication
      return showProgress();
    
    case 'result':
      // Process final result
      return processResult(data.args);
  }
});
```

### Component Integration Example

Here's a complete example of a custom component that handles command results:

```javascript
import { BaseEl } from '/chat/static/js/base.js';
import { html, css } from '/chat/static/js/lit-core.min.js';

class MyResultViewer extends BaseEl {
  static properties = {
    data: { type: Object }
  };

  static styles = css`
    :host {
      display: block;
      background: var(--component-bg, var(--background-color));
      color: var(--component-text, var(--text-color));
      padding: 1rem;
    }
  `;

  constructor() {
    super();
    this.data = {};
  }

  _render() {
    return html`
      <div class="result-viewer">
        <h3>${this.data.title}</h3>
        <pre>${JSON.stringify(this.data.content, null, 2)}</pre>
      </div>
    `;
  }
}

customElements.define('my-result-viewer', MyResultViewer);

// Register command handler
window.registerCommandHandler('show_result', (data) => {
  if (data.event === 'result') {
    return html`<my-result-viewer .data=${data.args}></my-result-viewer>`;
  }
  return null;
});
```

### Styling Guidelines

Components should use CSS custom properties for theming to maintain consistency with the core system:

```css
:host {
  /* Use theme variables with fallbacks */
  background: var(--component-bg, var(--background-color));
  color: var(--component-text, var(--text-color));
  padding: var(--component-padding, 1rem);
}
```

Common theme variables:
- `--background-color` - Main background
- `--text-color` - Main text color
- `--link-color` - Link text color
- `--code-bg` - Code block background
- `--component-bg` - Component background (can override --background-color)
- `--component-text` - Component text (can override --text-color)

Components should:
- Use CSS custom properties for themeable values
- Provide fallbacks to core theme variables
- Follow existing component patterns
- Support both light and dark themes

### Best Practices

1. **Component Design**
- Extend BaseEl for consistent theming and functionality
- Override _render() instead of render()
- Use properties for reactive data
- Follow web component lifecycle methods

2. **Command Handling**
- Register handlers early in component initialization
- Handle all event types (partial, running, result)
- Provide appropriate loading indicators
- Clean up resources when component is disconnected

3. **Event System**
- Use this.dispatch() for custom events
- Bubble events appropriately (bubbles: true)
- Include relevant detail data
- Listen for events at appropriate level

4. **Performance**
- Throttle frequent updates
- Use efficient rendering patterns
- Clean up event listeners and intervals
- Handle large data sets appropriately

5. **Integration**
- Follow existing component patterns
- Use theme variables consistently
- Support both desktop and mobile layouts
- Test with different themes and configurations

### Frontend Plugin Integration Points

Plugins can integrate with the frontend in several ways:

1. **Custom Components**
- Create new web components extending BaseEl
- Add to chat interface or custom pages
- Interact with command system
- Provide specialized visualizations

2. **Command Handlers**
- Register handlers for plugin commands
- Process command events (partial/running/result)
- Update UI in response to commands
- Handle command parameters and results

3. **Template Injection**
- Add content to existing template blocks
- Inject custom styles and scripts
- Extend core UI functionality
- Add new UI sections

4. **Static Assets**
- JavaScript modules and components
- CSS styles and themes
- Images and media
- Third-party dependencies

All static assets should be placed in the plugin's static/ directory and will be automatically mounted at /static/plugins/plugin_name/.

### Development Tips

1. **Getting Started**
- Study the core component implementations in the source files
- Use the browser dev tools to inspect component structure
- Test components in isolation before integration
- Start with simple components and build up complexity

2. **Debugging**
- Use console.log() in command handlers and component methods
- Inspect component properties and state in dev tools
- Watch for event propagation issues
- Check for proper cleanup in disconnectedCallback()

3. **Common Issues**
- Not extending BaseEl (missing theme support)
- Overriding render() instead of _render()
- Forgetting to handle all command event types
- Not cleaning up event listeners
- Missing theme variable fallbacks

4. **Testing**
- Test with different themes
- Verify mobile responsiveness
- Check memory usage with long sessions
- Validate command handler behavior
- Test component lifecycle methods

### SSE (Server-Sent Events) Integration

MindRoot uses SSE for real-time updates from the AI. The chat component establishes an SSE connection and listens for events:

- 'partial_command' - Incremental command output
- 'running_command' - Command execution status
- 'command_result' - Final command results
- 'image' - Image generation results
- 'finished_chat' - Chat completion

Plugins can utilize this system by:
1. Sending events from backend commands
2. Handling events in frontend components
3. Using the existing chat message display system
4. Adding custom event types if needed

### AI Integration Points

Components can interact with the AI system in several ways:

1. **Command Results**
- Display command outputs in custom formats
- Show progress for long-running operations
- Handle specialized data types
- Provide interactive UI for results

2. **Message Display**
- Customize how AI responses appear
- Add interactive elements to messages
- Handle special content types
- Provide context-specific visualizations

3. **Input Handling**
- Add custom input methods
- Pre-process user input
- Provide specialized interfaces
- Handle file uploads or other data

4. **Context Management**
- Access session context
- Store component-specific state
- Share data between components
- Maintain conversation history
## Tool Commands

Commands are Python functions that can be called by the AI agent. These must be:
1. Decorated with @command()
2. Listed in plugin_info.json
3. Enabled for specific agents in the /admin interface

Example command:

```python
from lib.providers.commands import command

@command()
async def read(fname, context=None):
    """Read text from a file.
    You must specify the full path to the file.
    
    Example:
    { "read": { "fname": "/path/to/file1.txt" } }
    """
    with open(fname, 'r') as f:
        text = f.read()
        return text
```

Key points about commands:
- Must be async functions
- Should include detailed docstrings with examples
- Can access context parameter for session data
- Should handle errors gracefully
- Can return data that the AI can use
- Must be enabled per-agent in admin interface

## setup.py and plugin install

IMPORTANT: **setup.py must handle install/inclusion of any files in subdirs, e.g. `static/`, `templates/`, `inject/`**

Example:

```shell
...
    package_data={
        "mr_pkg1": [
            "static/js/*.js",
            "static/*.js"
            "inject/*.jinja2",
            "override/*.jinja2"
        ],
    },
 ...

```


## Plugin Integration Points

1. **Commands**
   - Available to the AI through the command system
   - Registered via Python decorators
   - Can access context and services
   - Must be listed in plugin_info.json

2. **Services**
   - Similar to commands but for internal use
   - Registered via service decorator
   - Must be listed in plugin_info.json
   - Can be accessed by commands or other services

3. **Routes**
   - FastAPI endpoints for HTTP interactions
   - Automatically mounted if router.py exists
   - No configuration needed in plugin_info.json

4. **UI Integration**
   - inject/ - Templates appended to existing blocks
   - override/ - Templates replacing existing blocks
   - static/ - Automatically mounted static assets
   - Flexible frontend technology choice

## Development Workflow

1. Create plugin structure using modern Python package layout
2. Define plugin metadata in plugin_info.json
3. Implement commands and services in mod.py
4. Create router.py if API endpoints are needed
5. Add UI components and templates as needed
6. Ensure proper __init__.py imports
7. Install plugin with pip install -e .

## Best Practices

1. Use appropriate decorators for commands and services
2. Follow modern Python package structure
3. Choose appropriate frontend technology for needs
4. Properly scope static assets
5. Document commands and services
6. Include proper type hints and docstrings

## Common Patterns

1. **State Management**
   - Components can maintain local state
   - Backend can store state in context
   - API endpoints for state synchronization

2. **UI Updates**
   - Components handle real-time updates
   - Event-based communication
   - API polling for data updates

3. **Theme Integration**
   - Use CSS variables for theming
   - Respect existing style patterns
   - Consider dark/light mode support


## AI System Integration

Plugins can integrate with the AI system through:

1. **Commands**
   - Return structured data for UI rendering
   - Support streaming/partial results
   - Access conversation context
   - Handle file operations and external services

2. **Context Management**
   - Store plugin-specific data in context
   - Access user session information
   - Share state between commands
   - Maintain conversation history

3. **Event System**
   - Send SSE events from commands
   - Update UI in real-time
   - Stream command results
   - Handle long-running operations

## Pipeline System

MindRoot includes a pipeline system for processing data at different stages. Pipes allow plugins to modify or transform data as it flows through the system.

### Pipe Decorator

```python
from lib.pipelines.pipe import pipe

@pipe(name='filter_messages', priority=8)
def my_pipeline(data: dict, context=None) -> dict:
    # Modify or process data
    return data
```

### Pipeline Stages
- pre_process_msg - Before message processing
- process_results - After command execution
- Custom stages as needed

### Priority System
- Higher numbers run earlier
- Lower numbers run later
- Use priority to control execution order

Example use cases:
- Transform message content
- Add context information
- Filter or modify results
- Integrate with external systems
