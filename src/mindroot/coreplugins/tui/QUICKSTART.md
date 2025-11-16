# MindRoot TUI Quick Start

## 5-Minute Setup

### 1. Install MindRoot (if not already installed)

```bash
cd /files/mindroot
pip install -e .
```

### 2. Get Your API Key

**Option A: From Running Server**

1. Start MindRoot server:
   ```bash
   mindroot
   ```

2. Open browser: `http://localhost:8010`

3. Login/Signup

4. Go to: Settings → API Keys → Generate New Key

5. Copy the key

**Option B: From Command Line**

```bash
# Start server in background
mindroot &

# Wait a moment, then visit the web interface
# Or use the API directly if you have credentials
```

### 3. Set Your API Key

**Quick (current session only):**
```bash
export MINDROOT_API_KEY=your_key_here
```

**Permanent (recommended):**
```bash
# Add to your shell profile
echo 'export MINDROOT_API_KEY=your_key_here' >> ~/.bashrc
source ~/.bashrc

# Or create .env file
echo 'MINDROOT_API_KEY=your_key_here' > .env
```

### 4. Start Chatting!

```bash
mr
```

That's it! You're now chatting with your AI agent.

## Common Commands

```bash
# Interactive chat (default agent)
mr

# Chat with specific agent
mr --agent CodeHelper

# Quick task (non-interactive)
mr task "What is 2+2?"

# Task with file input
mr task "Summarize this" --input document.txt

# Help
mr --help
```

## Keyboard Shortcuts

- `Ctrl+Enter` - Send message
- `Ctrl+C` or `Ctrl+Q` - Quit
- `↑` / `↓` - Scroll chat

## Troubleshooting

### "API key not set"
```bash
# Check if set
echo $MINDROOT_API_KEY

# Set it
export MINDROOT_API_KEY=your_key_here
```

### "Connection refused"
```bash
# Make sure server is running
mindroot

# In another terminal
mr
```

### "Module not found"
```bash
# Reinstall
cd /files/mindroot
pip install -e .
```

## Next Steps

- Read the full guide: `TUI_GUIDE.md`
- Try different agents: `mr --agent CodeHelper`
- Automate tasks: `mr task "your task here"`
- Explore examples in the guide

## Examples

### Code Help
```bash
mr --agent CodeHelper
> Write a Python function to sort a list
```

### Quick Answer
```bash
mr task "Explain quantum computing in one sentence"
```

### File Processing
```bash
mr task "Summarize this document" --input report.txt
```

### Data Analysis
```bash
mr task "Analyze this CSV" --input data.csv --agent DataAnalyst
```

Enjoy using MindRoot TUI! 🚀
