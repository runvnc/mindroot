# MindRoot TUI Guide

Complete guide for using the MindRoot Terminal User Interface (`mr` command).

## Quick Start

1. **Install MindRoot** (if not already installed):
   ```bash
   cd /files/mindroot
   pip install -e .
   ```

2. **Set your API key**:
   ```bash
   export MINDROOT_API_KEY=your_api_key_here
   ```

3. **Start chatting**:
   ```bash
   mr
   ```

## Getting an API Key

1. Start the MindRoot server:
   ```bash
   mindroot
   ```

2. Open your browser to `http://localhost:8010`

3. Log in or create an account

4. Go to Settings → API Keys

5. Generate a new API key

6. Copy the key and set it in your environment:
   ```bash
   export MINDROOT_API_KEY=your_key_here
   ```

## Configuration

### Environment Variables

Create a `.env` file in your project directory:

```bash
# Required
MINDROOT_API_KEY=your_api_key_here

# Optional
MINDROOT_BASE_URL=http://localhost:8010
MINDROOT_DEFAULT_AGENT=Assistant
```

### System-wide Configuration

For system-wide settings, add to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export MINDROOT_API_KEY=your_api_key_here
export MINDROOT_BASE_URL=http://localhost:8010
export MINDROOT_DEFAULT_AGENT=Assistant
```

## Usage Modes

### Interactive Chat Mode

The default mode provides a full-featured chat interface:

```bash
# Default agent
mr

# Specific agent
mr --agent CodeHelper
mr -a DataAnalyst

# Different server
mr --url https://your-server.com
```

**Features:**
- Real-time streaming responses
- Command execution visualization
- Markdown rendering
- Syntax highlighting for code
- Scrollable chat history

### Task Mode (CLI)

For automation and scripting, use task mode:

```bash
# Simple task
mr task "What is 2+2?"

# With specific agent
mr task "Write a Python function" --agent CodeHelper

# Read from file
mr task "Analyze this" --input data.txt

# Pipe input
cat data.txt | mr task "Summarize this"
```

**Use Cases:**
- CI/CD pipelines
- Automated reports
- Batch processing
- Shell scripts

## Interface Overview

```
┌─────────────────────────────────────────────────────────────┐
│ MindRoot - Agent: Assistant                    [Ctrl+Q]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Chat History                                                │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ You                                                 │   │
│ │ Hello, can you help me with Python?                │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ Assistant                                           │   │
│ │ Of course! I'd be happy to help with Python.       │   │
│ │ What would you like to know?                       │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────┐   │
│ │ ⚙️ write                                            │   │
│ │ Writing file: /tmp/example.py                      │   │
│ │ ✅ Complete                                         │   │
│ └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ > Type your message... [Ctrl+Enter to send]                │
└─────────────────────────────────────────────────────────────┘
```

## Command Status Indicators

The TUI shows real-time status of agent commands:

| Icon | Status | Description |
|------|--------|-------------|
| 🔄 | Partial | Command is streaming/building |
| ⚙️ | Running | Command is executing |
| ✅ | Complete | Command finished successfully |
| ❌ | Error | Command failed |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Quit application |
| `Ctrl+Q` | Quit application |
| `Ctrl+Enter` | Send message |
| `↑` / `↓` | Scroll chat history |
| `Tab` | Focus next element |
| `Shift+Tab` | Focus previous element |

## Advanced Usage

### Multiple Agents

Switch between different agents for specialized tasks:

```bash
# Code assistance
mr --agent CodeHelper

# Data analysis
mr --agent DataAnalyst

# Writing assistance
mr --agent Writer
```

### Remote Servers

Connect to MindRoot instances on different servers:

```bash
# Production server
mr --url https://mindroot.example.com

# Development server
mr --url http://dev.local:8010

# With custom agent
mr --url https://mindroot.example.com --agent CustomAgent
```

### Scripting with Task Mode

**Example 1: Automated Code Review**

```bash
#!/bin/bash
# review.sh - Automated code review script

for file in src/*.py; do
    echo "Reviewing $file..."
    mr task "Review this Python code for issues" --input "$file" --agent CodeHelper
done
```

**Example 2: Daily Report Generation**

```bash
#!/bin/bash
# daily_report.sh

DATE=$(date +%Y-%m-%d)
mr task "Generate a summary report for $DATE" --input logs/$DATE.log --agent DataAnalyst > reports/$DATE.md
```

**Example 3: Batch Processing**

```bash
#!/bin/bash
# process_documents.sh

find documents/ -name "*.txt" | while read doc; do
    mr task "Summarize this document" --input "$doc" > "summaries/$(basename $doc .txt)_summary.txt"
done
```

## Troubleshooting

### Common Issues

#### 1. API Key Not Found

**Error:**
```
Error: MINDROOT_API_KEY environment variable not set
```

**Solution:**
```bash
# Check if key is set
echo $MINDROOT_API_KEY

# Set the key
export MINDROOT_API_KEY=your_key_here

# Or add to .env file
echo "MINDROOT_API_KEY=your_key_here" >> .env
```

#### 2. Connection Refused

**Error:**
```
Error connecting: Connection refused
```

**Solution:**
```bash
# Check if server is running
curl http://localhost:8010

# Start the server
mindroot

# Or specify correct URL
mr --url http://localhost:8010
```

#### 3. Invalid API Key

**Error:**
```
Error: Invalid API key
```

**Solution:**
- Generate a new API key from the web interface
- Make sure you copied the entire key
- Check for extra spaces or newlines

#### 4. Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'textual'
```

**Solution:**
```bash
# Reinstall MindRoot
cd /files/mindroot
pip install -e .

# Or install textual directly
pip install textual
```

### Debug Mode

Enable debug output:

```bash
# Set debug environment variable
export MR_DEBUG=1
mr

# Or with Python logging
export PYTHONVERBOSE=1
mr
```

## Tips and Best Practices

### 1. Use Task Mode for Automation

Task mode is perfect for:
- CI/CD pipelines
- Cron jobs
- Shell scripts
- Batch processing

### 2. Choose the Right Agent

Different agents are optimized for different tasks:
- **CodeHelper**: Programming and debugging
- **DataAnalyst**: Data analysis and visualization
- **Writer**: Content creation and editing
- **Assistant**: General purpose

### 3. Save Your Configuration

Create a `.env` file in your project:
```bash
MINDROOT_API_KEY=your_key
MINDROOT_DEFAULT_AGENT=CodeHelper
```

### 4. Use Aliases

Add to your shell profile:
```bash
alias mrc='mr --agent CodeHelper'
alias mrd='mr --agent DataAnalyst'
alias mrt='mr task'
```

### 5. Pipe and Redirect

Combine with other tools:
```bash
# Analyze git log
git log --oneline | mr task "Summarize these commits"

# Process and save
mr task "Analyze this" --input data.csv > analysis.md

# Chain commands
cat input.txt | mr task "Translate to Spanish" | mr task "Summarize"
```

## Examples

### Code Generation

```bash
mr --agent CodeHelper
> Write a Python function to calculate the Fibonacci sequence
```

### Data Analysis

```bash
mr task "Analyze this CSV and provide insights" --input sales_data.csv --agent DataAnalyst
```

### Content Creation

```bash
mr --agent Writer
> Write a blog post about AI in healthcare
```

### Quick Questions

```bash
mr task "What is the capital of France?"
mr task "Explain quantum computing in simple terms"
mr task "Convert 100 USD to EUR"
```

### File Processing

```bash
# Summarize a document
mr task "Summarize this document" --input report.txt

# Code review
mr task "Review this code for bugs" --input app.py --agent CodeHelper

# Translate
mr task "Translate to Spanish" --input english.txt
```

## Integration Examples

### Git Hooks

**pre-commit hook:**
```bash
#!/bin/bash
# .git/hooks/pre-commit

for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    mr task "Quick code review" --input "$file" --agent CodeHelper
done
```

### CI/CD Pipeline

**GitHub Actions:**
```yaml
name: AI Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install MindRoot
        run: pip install mindroot
      - name: Review Code
        env:
          MINDROOT_API_KEY: ${{ secrets.MINDROOT_API_KEY }}
        run: |
          mr task "Review this PR" --input changes.diff --agent CodeHelper
```

### Cron Jobs

```bash
# Daily report at 9 AM
0 9 * * * cd /path/to/project && mr task "Generate daily report" --input logs/$(date +\%Y-\%m-\%d).log > reports/daily.md

# Weekly summary on Fridays
0 17 * * 5 cd /path/to/project && mr task "Generate weekly summary" --agent DataAnalyst > reports/weekly.md
```

## Performance Tips

1. **Use Task Mode for Single Queries**: Faster startup than interactive mode
2. **Keep Sessions Short**: Long conversations use more tokens
3. **Choose Appropriate Agents**: Specialized agents are more efficient
4. **Use Local Server**: Reduce network latency

## Security Considerations

1. **Protect Your API Key**: Never commit to version control
2. **Use Environment Variables**: Don't hardcode keys in scripts
3. **Rotate Keys Regularly**: Generate new keys periodically
4. **Limit Key Permissions**: Use read-only keys when possible
5. **Use HTTPS**: Always use secure connections for remote servers

## Getting Help

```bash
# Show help
mr --help

# Task mode help
mr task --help

# Check version
mr --version
```

## Contributing

The TUI is part of MindRoot core. To contribute:

1. Fork the repository
2. Make changes in `src/mindroot/coreplugins/tui/`
3. Test thoroughly
4. Submit a pull request

## Roadmap

- [ ] Session management (save/load/list)
- [ ] Search conversation history
- [ ] Export conversations (markdown, JSON, PDF)
- [ ] Multiple themes (dark, light, custom)
- [ ] Image display in terminal
- [ ] File upload support
- [ ] Voice input/output
- [ ] Multi-agent conversations
- [ ] Plugin system for custom commands
- [ ] Configuration UI

## License

Same as MindRoot - see LICENSE file in the main repository.
