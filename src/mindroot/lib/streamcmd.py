#!/usr/bin/env python3

import asyncio
import sys
from typing import Optional, Callable, Any, List, Dict, AsyncGenerator

# ANSI color codes for terminal output
COLORS = {
    'reset': '\033[0m',
    'green': '\033[32m',  # stdout
    'yellow': '\033[33m',  # stderr/warning
    'blue': '\033[34m',    # info
    'red': '\033[31m'      # error
}


async def read_stream(stream: asyncio.StreamReader, callback: Callable[[str], Any]):
    """Read from stream line by line and call the callback for each line."""
    while True:
        line = await stream.readline()
        if not line:
            break
        callback(line.decode('utf-8', errors='replace'))


async def run_command_with_streaming(
    cmd: List[str],
    stdout_callback: Callable[[str], Any],
    stderr_callback: Callable[[str], Any],
    cwd: Optional[str] = None,
    env: Optional[dict] = None
) -> int:
    """Run a command asynchronously and stream its output.
    
    Args:
        cmd: Command to run as a list of strings
        stdout_callback: Callback for stdout lines
        stderr_callback: Callback for stderr lines
        cwd: Working directory for the command
        env: Environment variables for the command
        
    Returns:
        Exit code of the command
    """
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env
        )
        
        # Create tasks to read from stdout and stderr
        stdout_task = asyncio.create_task(
            read_stream(process.stdout, stdout_callback)
        )
        stderr_task = asyncio.create_task(
            read_stream(process.stderr, stderr_callback)
        )
        
        # Wait for the process to complete and streams to be fully read
        await asyncio.gather(stdout_task, stderr_task)
        exit_code = await process.wait()
        
        return exit_code
        
    except Exception as e:
        print(f"Failed to run command: {e}")
        return 1


async def stream_command_as_events(
    cmd: List[str],
    cwd: Optional[str] = None,
    env: Optional[dict] = None
) -> AsyncGenerator[Dict[str, str], None]:
    """Run a command and yield its output as events.
    
    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory for the command
        env: Environment variables for the command
        
    Yields:
        Events with type and data
    """
    # Debug output
    print(f"{COLORS['blue']}[DEBUG] Running command: {' '.join(cmd)}{COLORS['reset']}")
    
    # Send initial event
    yield {"event": "message", "data": f"Running command: {' '.join(cmd)}"}
    
    # Create queues for stdout and stderr
    output_queue = asyncio.Queue()
    
    # Define callbacks for stdout and stderr
    def stdout_callback(line):
        if line.strip():
            print(f"{COLORS['green']}[STDOUT] {line.strip()}{COLORS['reset']}")
            output_queue.put_nowait(("message", line.strip()))
    
    def stderr_callback(line):
        if line.strip():
            # Determine if this is a warning or an error
            if ("WARNING:" in line or 
                "DEPRECATION:" in line or 
                "A new release of pip is available" in line):
                print(f"{COLORS['yellow']}[WARNING] {line.strip()}{COLORS['reset']}")
                output_queue.put_nowait(("warning", line.strip()))
            else:
                print(f"{COLORS['red']}[ERROR] {line.strip()}{COLORS['reset']}")
                output_queue.put_nowait(("warning", line.strip()))
    
    # Run the command in a separate task
    run_task = asyncio.create_task(
        run_command_with_streaming(cmd, stdout_callback, stderr_callback, cwd, env)
    )
    
    # Stream events from the queue while the command is running
    while not run_task.done() or not output_queue.empty():
        try:
            event_type, data = await asyncio.wait_for(output_queue.get(), timeout=0.1)
            yield {"event": event_type, "data": data}
        except asyncio.TimeoutError:
            # No output available, just continue
            await asyncio.sleep(0.01)
    
    # Get the exit code
    exit_code = await run_task
    
    # Send completion event
    print(f"{COLORS['blue']}[INFO] Command completed with exit code {exit_code}{COLORS['reset']}")
    if exit_code == 0:
        yield {"event": "complete", "data": "Command completed successfully"}
    else:
        print(f"{COLORS['red']}[ERROR] Command failed with exit code {exit_code}{COLORS['reset']}")
        yield {"event": "error", "data": f"Command failed with exit code {exit_code}"}

