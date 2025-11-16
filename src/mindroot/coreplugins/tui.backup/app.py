"""Main TUI application using Textual."""

import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Button, Label
from textual.binding import Binding
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from .client import MindRootClient
from rich.markup import escape
import sys
import json
import pyperclip
import os
import traceback


class MessageWidget(Static):
    """Widget to display a single message."""
    
    def __init__(self, role: str, content: str, message_id: int = None, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content  # This is the raw text content
        self.raw_content = content  # Store raw content for copying
        self.message_id = message_id
        self.can_focus = True  # Make the widget focusable
        self.is_code = False  # Track if this is code content
        self.update_content()
    
    def set_content(self, content: str):
        """Update the content and re-render."""
        self.content = content
        self.raw_content = content
        self.update_content()
        # Don't force refresh here - let Textual handle it
        # self.refresh()
    
    def update_content(self):
        """Update the displayed content."""
        if self.role == "user":
            style = "bold cyan"
            prefix = "You"
        elif self.role == "system":
            style = "bold yellow"
            prefix = "System"
        else:
            style = "bold green"
            prefix = "Assistant"
        
        content = self.content
        
        # Try to render as markdown
        try:
            
            # Check for problematic patterns that might crash Rich's markdown parser
            # Empty content or just whitespace
            if not content or not content.strip():
                content = "(empty message)"
                self.update(Panel(content, title=f"[{style}]{prefix}[/{style}]", border_style=style))
                return
            
            # Check if content is a code block (starts with ```)
            if content.strip().startswith('```'):
                # Extract language and code from markdown code block
                lines = content.strip().split('\n')
                first_line = lines[0]
                language = first_line[3:].strip() if len(first_line) > 3 else 'text'
                
                # Get the code content (everything between ``` markers)
                if len(lines) > 2 and lines[-1].strip() == '```':
                    code_content = '\n'.join(lines[1:-1])
                else:
                    code_content = '\n'.join(lines[1:])
                
                # Use Syntax for code highlighting (doesn't interpret Rich markup)
                try:
                    syntax = Syntax(code_content, language, theme="monokai", line_numbers=False)
                    self.update(Panel(syntax, title=f"[{style}]{prefix}[/{style}]", border_style=style))
                except Exception as syntax_error:
                    # If Syntax fails, fall back to plain text
                    plain_text = Text(code_content, style="dim")
                    self.update(Panel(plain_text, title=f"[{style}]{prefix} (code)[/{style}]", border_style=style))
            else:
                # For non-code content, escape and render as markdown
                try:
                    escaped_content = escape(content)
                    md = Markdown(escaped_content)
                    self.update(Panel(md, title=f"[{style}]{prefix}[/{style}]", border_style=style))
                except Exception as md_error:
                    # If markdown fails, use plain text
                    plain_text = Text(escape(content))
                    self.update(Panel(plain_text, title=f"[{style}]{prefix}[/{style}]", border_style=style))
            
        except Exception as e:
            # Fallback to plain text with error info
            try:
                # Use plain Text object - safest option
                error_text = Text(f"[Render Error: {type(e).__name__}]\n\n", style="red")
                content_text = Text(self.content if self.content else "(empty)")
                combined = error_text + content_text
                self.update(Panel(combined, title=f"[{style}]{prefix}[/{style}]", border_style=style))
            except:
                # Absolute last resort - plain string
                self.update(Panel("[Content could not be rendered]", title=f"[{style}]{prefix}[/{style}]", border_style=style))
    
    def on_click(self) -> None:
        """Handle click to copy message."""
        try:
            pyperclip.copy(self.raw_content)
            self.app.notify("Copied to clipboard!", severity="information")
        except Exception as e:
            self.app.notify(f"Failed to copy: {str(e)}", severity="error")


class CommandWidget(Static):
    """Widget to display command execution status."""
    
    def __init__(self, command: str, status: str = "running", **kwargs):
        super().__init__(**kwargs)
        self.command = command
        self.status = status
        self.params = {}
        self.result = None
        self.update_display()
    
    def update_display(self):
        """Update the command display based on status."""
        if self.status == "partial":
            icon = "🔄"
            style = "yellow"
        elif self.status == "running":
            icon = "⚙️"
            style = "blue"
        elif self.status == "complete":
            icon = "✅"
            style = "green"
        elif self.status == "error":
            icon = "❌"
            style = "red"
        else:
            icon = "❓"
            style = "white"
        
        title = f"[{style}]{icon} {self.command}[/{style}]"
        
        # Build content
        content_parts = []
        if self.params:
            content_parts.append(f"Parameters: {self.params}")
        if self.result:
            content_parts.append(f"Result: {self.result}")
        
        content = "\n".join(content_parts) if content_parts else "Executing..."
        
        self.update(Panel(content, title=title, border_style=style))


class ChatView(ScrollableContainer):
    """Scrollable container for chat messages."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.messages = []
        self.commands = {}
    
    def add_message(self, role: str, content: str):
        """Add a message to the chat."""
        message_id = len(self.messages)
        msg = MessageWidget(role, content, message_id=message_id)
        self.mount(msg)
        self.messages.append(msg)
        self.scroll_end(animate=False)
        return msg
    
    def add_command(self, command_id: str, command: str):
        """Add a command widget."""
        cmd = CommandWidget(command)
        self.mount(cmd)
        self.commands[command_id] = cmd
        self.scroll_end(animate=False)
        return cmd
    
    def get_last_assistant_message(self):
        """Get the last assistant message widget."""
        for msg in reversed(self.messages):
            if msg.role == "assistant":
                return msg
        return None
    
    def update_command(self, command_id: str, status: str, params=None, result=None):
        """Update a command's status."""
        if command_id in self.commands:
            cmd = self.commands[command_id]
            cmd.status = status
            if params:
                cmd.params = params
            if result:
                cmd.result = result
            cmd.update_display()


class MindRootTUI(App):
    """Main TUI application."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    ChatView {
        height: 1fr;
        border: solid green;
    }
    
    #input-container {
        height: auto;
        dock: bottom;
        background: $surface;
    }
    
    Input {
        width: 1fr;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
        Binding("ctrl+y", "copy_last_message", "Copy Last", show=True),
    ]
    
    def __init__(self, agent_name: str = "Assistant", debug: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self.debug_mode = debug
        self.client = None
        self.log_id = None
        self.current_message = ""
        self.event_task = None
        self.current_assistant_widget = None
    
    def on_exception(self, exception: Exception) -> None:
        """Global exception handler to prevent crashes."""
        try:
            chat_view = self.query_one("#chat-view", ChatView)
            error_msg = f"[ERROR] {type(exception).__name__}: {str(exception)}"
            if self.debug_mode:
                error_msg += f"\n\n{traceback.format_exc()}"
            chat_view.add_message("system", error_msg)
        except:
            # If we can't even add a message, just log it
            print(f"FATAL ERROR: {exception}")
            print(traceback.format_exc())
    
    def action_copy_last_message(self) -> None:
        """Copy the last assistant message to clipboard."""
        chat_view = self.query_one("#chat-view", ChatView)
        last_msg = chat_view.get_last_assistant_message()
        if last_msg:
            try:
                pyperclip.copy(last_msg.raw_content)
                self.notify("✓ Last message copied to clipboard!", severity="information")
            except Exception as e:
                self.notify(f"Failed to copy: {str(e)}", severity="error")
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield ChatView(id="chat-view")
        with Horizontal(id="input-container"):
            yield Input(placeholder="Type your message... (Ctrl+Enter to send)", id="message-input")
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize the app."""
        self.title = f"MindRoot - {self.agent_name}"
        chat_view = self.query_one("#chat-view", ChatView)
        
        # Initialize client and create session
        try:
            if self.debug_mode:
                chat_view.add_message("system", "Debug mode enabled")
            
            self.client = MindRootClient(debug=self.debug_mode)
            
            chat_view.add_message("system", f"Connecting to {self.agent_name}...")
            
            self.log_id = await self.client.create_session(self.agent_name, client_cwd=os.getcwd())
            
            chat_view.add_message("system", f"Connected! Session: {self.log_id}")
            
            if self.debug_mode:
                chat_view.add_message("system", f"Starting event listener...")
            
            # Start listening for events
            self.event_task = asyncio.create_task(self.listen_for_events())
            
        except Exception as e:
            error_msg = f"Error connecting: {str(e)}"
            chat_view.add_message("system", error_msg)
            if self.debug_mode:
                chat_view.add_message("system", f"Traceback:\n{traceback.format_exc()}")
        
        # Focus the input box
        input_widget = self.query_one("#message-input", Input)
        input_widget.focus()
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message submission."""
        message = event.value.strip()
        if not message:
            return
        
        # Clear input
        event.input.value = ""
        
        # Add user message to chat
        chat_view = self.query_one("#chat-view", ChatView)
        chat_view.add_message("user", message)
        
        if self.debug_mode:
            chat_view.add_message("system", f"Sending message to log_id: {self.log_id}")
        
        # Send message to agent
        try:
            result = await self.client.send_message(self.log_id, message)
            if self.debug_mode:
                chat_view.add_message("system", f"Send result: {result}")
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            chat_view.add_message("system", error_msg)
            if self.debug_mode:
                chat_view.add_message("system", f"Traceback:\n{traceback.format_exc()}")
    
    async def listen_for_events(self):
        """Listen for SSE events from the agent."""
        chat_view = self.query_one("#chat-view", ChatView)
        current_command_id = None
        
        try:
            if self.debug_mode:
                chat_view.add_message("system", "Event listener started")
            
            def extract_text_from_data(data):
                """Extract text from data object, mimicking web UI's textParam function."""
                # Check args first
                if isinstance(data.get('args'), dict):
                    if 'text' in data['args']:
                        return data['args']['text']
                    elif 'markdown' in data['args']:
                        return data['args']['markdown']
                
                # Check params
                if isinstance(data.get('params'), dict):
                    if 'text' in data['params']:
                        return data['params']['text']
                    elif 'markdown' in data['params']:
                        return data['params']['markdown']
                    elif 'extensive_chain_of_thoughts' in data['params']:
                        return data['params']['extensive_chain_of_thoughts']
                
                # Fallback to chunk if present
                return data.get('chunk', '')
            
            async for event in self.client.stream_events(self.log_id):
                event_type = event["event"]
                data = event["data"]
                
                if self.debug_mode:
                    chat_view.add_message("system", f"Event: {event_type}")
                
                if event_type == "partial_command":
                    command = data.get("command")
                    
                    # Extract text using the same logic as web UI
                    text_content = extract_text_from_data(data)
                    
                    # For write/append/overwrite commands, detect code and wrap in code blocks
                    if command in ["write", "append", "overwrite"]:
                        # Check if content looks like code
                        is_code = False
                        language = None
                        
                        # Simple heuristics for code detection
                        if any(keyword in text_content for keyword in ['def ', 'class ', 'import ', 'from ', 'function ', 'const ', 'let ', 'var ', 'public ', 'private ']):
                            is_code = True
                            if any(kw in text_content for kw in ['def ', 'class ', 'import ', 'from ']):
                                language = 'python'
                            elif any(kw in text_content for kw in ['function ', 'const ', 'let ', 'var ']):
                                language = 'javascript'
                            elif any(kw in text_content for kw in ['public ', 'private ', 'class ']):
                                language = 'java'
                        elif text_content.strip().startswith('<?php'):
                            is_code = True
                            language = 'php'
                        elif text_content.strip().startswith('<') and '>' in text_content:
                            is_code = True
                            language = 'html'
                        
                        # Wrap in code blocks if detected as code
                        if is_code and language:
                            text_content = f"```{language}\n{text_content}\n```"
                        elif is_code:
                            text_content = f"```\n{text_content}\n```"
                    
                    # For display commands including write/append/overwrite, stream the content
                    if command in ["say", "wait_for_user_reply", "markdown_await_user", "tell_and_continue", "write", "append", "overwrite"]:
                        # Create assistant message widget if it doesn't exist
                        if self.current_assistant_widget is None:
                            self.current_assistant_widget = chat_view.add_message("assistant", text_content)
                        else:
                            # Update existing widget with new content
                            self.current_assistant_widget.set_content(text_content)
                        
                        # Scroll to show the updated content
                        chat_view.scroll_end(animate=False)
                        
                        # Also store in current_message for later use
                        self.current_message = text_content
                    else:
                        # For other action commands, show command widget
                        if current_command_id is None:
                            current_command_id = f"{command}_{id(data)}"
                            chat_view.add_command(current_command_id, command)
                        chat_view.update_command(current_command_id, "partial", data.get('params', {}))
                
                elif event_type == "running_command":
                    command = data.get("command")
                    args = data.get("args", {})
                    
                    if command in ["say", "wait_for_user_reply", "markdown_await_user", "tell_and_continue", "write", "append", "overwrite"]:
                        # Message already created and updated during partial_command events
                        # Just clear the current widget reference
                        self.current_message = ""
                        self.current_assistant_widget = None
                    else:
                        if current_command_id is None:
                            current_command_id = f"{command}_{id(data)}"
                            chat_view.add_command(current_command_id, command)
                        chat_view.update_command(current_command_id, "running", args)
                
                elif event_type == "command_result":
                    command = data.get("command")
                    result = data.get("result")
                    
                    # Update command widget if it exists
                    if current_command_id:
                        chat_view.update_command(current_command_id, "complete", result=result)
                        current_command_id = None
                
                elif event_type == "finished_chat":
                    # Conversation turn complete
                    if self.current_message:
                        # If there's still a message that wasn't displayed, show it now
                        chat_view.add_message("assistant", self.current_message)
                        self.current_message = ""
                        self.current_assistant_widget = None
                    current_command_id = None
                    
                    if self.debug_mode:
                        chat_view.add_message("system", "Turn complete")
                
                elif event_type == "system_error":
                    error = data.get("error", "Unknown error")
                    chat_view.add_message("system", f"Error: {error}")
                    current_command_id = None
        
        except Exception as e:
            error_msg = f"Event stream error: {str(e)}"
            chat_view.add_message("system", error_msg)
            if self.debug_mode:
                chat_view.add_message("system", f"Traceback:\n{traceback.format_exc()}")
    
    async def on_unmount(self) -> None:
        """Cleanup when app closes."""
        if self.event_task:
            self.event_task.cancel()
        if self.client:
            await self.client.close()


def run_tui(agent_name: str = "Assistant", debug: bool = False):
    """Run the TUI application."""
    app = MindRootTUI(agent_name=agent_name, debug=debug)
    app.run()


if __name__ == "__main__":
    run_tui()
