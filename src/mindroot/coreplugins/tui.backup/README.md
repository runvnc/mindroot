# MindRoot TUI

A beautiful terminal user interface for interacting with MindRoot agents.

## Features

- 🎨 **Beautiful Terminal UI** - Built with Textual for a modern, responsive interface
- 💬 **Interactive Chat** - Real-time streaming responses from agents
- ⚡ **Command Visualization** - See agent commands execute with status indicators
- 📝 **Markdown Rendering** - Rich text formatting in the terminal
- 🔧 **Task Mode** - Run one-off tasks without interactive chat
- 🔐 **API Key Authentication** - Secure connection to MindRoot server

## Installation

The TUI is included with MindRoot. After installing MindRoot:

```bash
pip install -e .
```

The `mr` command will be available.

## Configuration

Set your API key in environment variables or `.env` file:

```bash
export MINDROOT_API_KEY=your_api_key_here
export MINDROOT_BASE_URL=http://localhost:8010  # optional, defaults to localhost
export MINDROOT_DEFAULT_AGENT=Assistant         # optional, defaults to Assistant
```

Or create a `.env` file:

```
MINDROOT_API_KEY=your_api_key_here
MINDROOT_BASE_URL=http://localhost:8010
MINDROOT_DEFAULT_AGENT=Assistant
```

## Usage

### Interactive Mode

Start a chat session with the default agent:

```bash
mr
```

Start with a specific agent:

```bash
mr --agent CodeHelper
mr -a DataAnalyst
```

Connect to a different server:

```bash
mr --url https://your-mindroot-server.com
```

### Task Mode (Non-Interactive)

Run a single task and get the result:

```bash
mr task "Analyze this data and provide insights"
```

With a specific agent:

```bash
mr task "Write a Python script to parse CSV" --agent CodeHelper
```

Read instructions from a file:

```bash
mr task "Summarize this document" --input document.txt
```

## Keyboard Shortcuts

- `Ctrl+C` or `Ctrl+Q` - Quit the application
- `Ctrl+Enter` - Send message (in input field)
- `Ctrl+L` - Clear screen (coming soon)
- `Ctrl+N` - New session (coming soon)

## Command Visualization

The TUI displays agent commands with status indicators:

- 🔄 **Partial** - Command is streaming/building
- ⚙️ **Running** - Command is executing
- ✅ **Complete** - Command finished successfully
- ❌ **Error** - Command failed

## Examples

### Basic Chat

```bash
$ mr
# Opens interactive chat with Assistant
```

### Code Generation

```bash
$ mr --agent CodeHelper
You: Write a Python function to calculate fibonacci numbers
# Agent responds with code and explanations
```

### Data Analysis

```bash
$ mr task "Analyze sales data" --input sales.csv --agent DataAnalyst
# Returns analysis results and exits
```

## Troubleshooting

### API Key Not Set

```
Error: MINDROOT_API_KEY environment variable not set
```

Solution: Set your API key in environment or `.env` file.

### Connection Refused

```
Error connecting: Connection refused
```

Solution: Make sure MindRoot server is running and the URL is correct.

### Module Not Found

```
ModuleNotFoundError: No module named 'textual'
```

Solution: Reinstall MindRoot with `pip install -e .`

## Development

The TUI is located in `src/mindroot/coreplugins/tui/`:

- `cli.py` - Command-line interface and argument parsing
- `app.py` - Main Textual application
- `client.py` - MindRoot API client
- `mod.py` - Plugin integration

## Future Features

- [ ] Session management (list, switch, resume)
- [ ] Search conversation history
- [ ] Export conversations
- [ ] Multiple themes
- [ ] Image display support
- [ ] File upload support
- [ ] Configuration UI

## License

Same as MindRoot - see main LICENSE file.
