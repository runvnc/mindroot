# MindRoot Plugin System

## Overview
The MindRoot plugin system is a modular architecture that combines Python backend functionality with web components for the frontend. It provides a flexible way to extend the system's capabilities through commands, services, and web UI components.

## Plugin Structure
```
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
{% block head_styles %}    {# CSS includes #}
{% block head_scripts %}   {# JavaScript includes #}
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

### 5. Frontend Integration

- Jinja2 templates are required for page rendering
- Frontend components can use any technology:
  - Lit web components (recommended for core components)
  - React with bundler
  - Vue
  - Plain JavaScript
  - Any other framework

Web components are especially recommended when:
- Injecting into core pages
- Building reusable UI components
- Creating core functionality

#### Static Assets
- Automatically mounted if static/ directory exists
- Available at /static/plugins/plugin_name/
- Can include any static files:
  - JavaScript modules
  - CSS
  - Images
  - Bundled applications

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
