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

### Plugin Integration Points

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