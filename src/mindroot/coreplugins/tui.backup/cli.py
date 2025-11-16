"""Command-line interface for MindRoot TUI."""

import argparse
import asyncio
import sys
import os
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import traceback

console = Console()


async def run_task_mode(agent_name: str, instructions: str, debug: bool = False):
    """Run a task in non-interactive mode and print the result."""
    try:
        from .client import MindRootClient
        
        if debug:
            console.print(f"[dim]Debug mode enabled[/dim]")
            console.print(f"[dim]Agent: {agent_name}[/dim]")
            console.print(f"[dim]Instructions length: {len(instructions)}[/dim]")
        
        client = MindRootClient(debug=debug)
        
        console.print(f"[bold cyan]Running task with {agent_name}...[/bold cyan]")
        
        console.print()
        
        # Pass client working directory to run_task
        result = await client.run_task(agent_name, instructions, client_cwd=os.getcwd())
        
        if debug:
            console.print(f"[dim]Result keys: {result.keys()}[/dim]")
        
        if result.get("status") == "ok":
            output = result.get("results", "No output")
            
            if debug:
                console.print(f"[dim]Output type: {type(output)}[/dim]")
            
            console.print(Panel(
                Markdown(str(output)),
                title="[bold green]Task Result[/bold green]",
                border_style="green"
            ))
            
            # Also print log_id for reference
            log_id = result.get("log_id")
            if log_id:
                console.print(f"\n[dim]Session ID: {log_id}[/dim]")
        else:
            error_msg = result.get('message', 'Unknown error')
            console.print(f"[bold red]Error:[/bold red] {error_msg}")
            if debug:
                console.print(f"[dim]Full result: {result}[/dim]")
            sys.exit(1)
        
        await client.close()
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        if debug:
            console.print(f"[dim]Traceback:[/dim]")
            console.print(traceback.format_exc())
        sys.exit(1)


def main():
    """Main entry point for the mr command."""
    parser = argparse.ArgumentParser(
        description="MindRoot TUI - Terminal interface for MindRoot agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive chat with default agent
  mr
  
  # Start chat with specific agent
  mr --agent CodeHelper
  
  # Run a task and exit (non-interactive)
  mr task "Analyze this data" --agent DataAnalyst
  
  # Run task with input from file
  mr task "Summarize this document" --input document.txt
  
  # Enable debug mode
  mr --debug task "test"

Environment Variables:
  MINDROOT_API_KEY      Your MindRoot API key (required)
  MINDROOT_BASE_URL     MindRoot server URL (default: http://localhost:8010)
  MINDROOT_DEFAULT_AGENT Default agent name (default: Assistant)
  MR_DEBUG              Enable debug mode (true/false)
        """
    )
    
    parser.add_argument(
        "--agent",
        "-a",
        default=os.getenv("MINDROOT_DEFAULT_AGENT", "Assistant"),
        help="Agent name to chat with (default: Assistant)"
    )
    
    parser.add_argument(
        "--url",
        default=os.getenv("MINDROOT_BASE_URL", "http://localhost:8010"),
        help="MindRoot server URL"
    )
    
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode with verbose output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Task command for non-interactive mode
    task_parser = subparsers.add_parser(
        "task",
        help="Run a task and exit (non-interactive mode)"
    )
    task_parser.add_argument(
        "instructions",
        help="Task instructions for the agent"
    )
    task_parser.add_argument(
        "--input",
        "-i",
        help="Read instructions from file instead"
    )
    
    args = parser.parse_args()
    
    # Enable debug mode from environment or flag
    debug = args.debug or os.getenv('MR_DEBUG', 'false').lower() == 'true'
    
    if debug:
        console.print("[yellow]Debug mode enabled[/yellow]")
        console.print(f"[dim]Agent: {args.agent}[/dim]")
        console.print(f"[dim]URL: {args.url}[/dim]")
    
    # Check for API key
    api_key = os.getenv("MINDROOT_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] MINDROOT_API_KEY environment variable not set")
        console.print("\nPlease set your API key:")
        console.print("  export MINDROOT_API_KEY=your_key_here")
        console.print("\nOr add it to your .env file")
        sys.exit(1)
    
    if debug:
        console.print(f"[dim]API key: {api_key[:10]}...[/dim]")
    
    # Set base URL if provided
    if args.url:
        os.environ["MINDROOT_BASE_URL"] = args.url
    
    # Handle commands
    if args.command == "task":
        # Task mode - non-interactive
        instructions = args.instructions
        
        # Read from file if specified
        if args.input:
            try:
                with open(args.input, 'r') as f:
                    file_content = f.read()
                instructions = f"{instructions}\n\n{file_content}"
            except Exception as e:
                console.print(f"[bold red]Error reading file:[/bold red] {str(e)}")
                sys.exit(1)
        
        # Run task
        asyncio.run(run_task_mode(args.agent, instructions, debug=debug))
    
    else:
        # Interactive mode - launch TUI
        try:
            from .app import run_tui
            
            if debug:
                console.print("[dim]Starting interactive TUI...[/dim]")
            
            run_tui(agent_name=args.agent, debug=debug)
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye![/dim]")
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            if debug:
                console.print(f"[dim]Traceback:[/dim]")
                console.print(traceback.format_exc())
            sys.exit(1)


if __name__ == "__main__":
    main()
