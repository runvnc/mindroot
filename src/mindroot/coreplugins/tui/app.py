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
import sys
import json
import traceback


class MessageWidget(Static):
    """Widget to display a single message."""
    
    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
        self.update_content()
    
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
        
        # Try to render as markdown
        try:
            md = Markdown(self.content)
            self.update(Panel(md, title=f"[{style}]{prefix}[/{style}]", border_style=style))
        except:
            # Fallback to plain text
            self.update(Panel(self.content, title=f"[{style}]{prefix}[/{style}]", border_style=style))


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
        msg = MessageWidget(role, content)
        self.mount(msg)
        self.messages.append(msg)
        self.scroll_end(animate=False)
    
    def add_command(self, command_id: str, command: str):
        """Add a command widget."""
        cmd = CommandWidget(command)
        self.mount(cmd)
        self.commands[command_id] = cmd
        self.scroll_end(animate=False)
        return cmd
    
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
    ]
    
    def __init__(self, agent_name: str = "Assistant", debug: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.agent_name = agent_name
        self.debug_mode = debug
        self.client = None
        self.log_id = None
        self.current_message = ""
        self.event_task = None
    
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
            
            self.log_id = await self.client.create_session(self.agent_name)
            
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
            
            async for event in self.client.stream_events(self.log_id):
                event_type = event["event"]
                data = event["data"]
                
                if self.debug_mode:
                    chat_view.add_message("system", f"Event: {event_type}")
                
                if event_type == "partial_command":
                    command = data.get("command")
                    chunk = data.get("chunk", "")
                    params = data.get("params", {})
                    
                    # For display commands, accumulate text
                    if command in ["say", "wait_for_user_reply", "markdown_await_user", "tell_and_continue"]:
                        self.current_message += chunk
                    else:
                        # For action commands, show command widget
                        if current_command_id is None:
                            current_command_id = f"{command}_{id(data)}"
                            chat_view.add_command(current_command_id, command)
                        chat_view.update_command(current_command_id, "partial", params)
                
                elif event_type == "running_command":
                    command = data.get("command")
                    args = data.get("args", {})
                    
                    if command in ["say", "wait_for_user_reply", "markdown_await_user", "tell_and_continue"]:
                        # Display accumulated message
                        if self.current_message:
                            # Check if message is just {"text": "..."} and extract the text
                            msg_to_display = self.current_message
                            try:
                                # Try to parse as JSON
                                parsed = json.loads(self.current_message.strip())
                                if isinstance(parsed, dict) and "text" in parsed and len(parsed) == 1:
                                    # If it's just {"text": "..."}, use the text value
                                    msg_to_display = parsed["text"]
                                    if self.debug_mode:
                                        chat_view.add_message("system", "Extracted text from JSON response")
                            except (json.JSONDecodeError, ValueError):
                                # Not JSON, use as-is
                                pass
                            
                            chat_view.add_message("assistant", msg_to_display)
                            self.current_message = ""
                    else:
                        if current_command_id is None:
                            current_command_id = f"{command}_{id(data)}"
                            chat_view.add_command(current_command_id, command)
                        chat_view.update_command(current_command_id, "running", args)
                
                elif event_type == "command_result":
                    command = data.get("command")
                    result = data.get("result")
                    
                    if current_command_id:
                        chat_view.update_command(current_command_id, "complete", result=result)
                        current_command_id = None
                
                elif event_type == "finished_chat":
                    # Conversation turn complete
                    if self.current_message:
                        # Check if message is just {"text": "..."} and extract the text
                        msg_to_display = self.current_message
                        try:
                            # Try to parse as JSON
                            parsed = json.loads(self.current_message.strip())
                            if isinstance(parsed, dict) and "text" in parsed and len(parsed) == 1:
                                # If it's just {"text": "..."}, use the text value
                                msg_to_display = parsed["text"]
                                if self.debug_mode:
                                    chat_view.add_message("system", "Extracted text from JSON response")
                        except (json.JSONDecodeError, ValueError):
                            # Not JSON, use as-is
                            pass
                        
                        chat_view.add_message("assistant", msg_to_display)
                        self.current_message = ""
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
