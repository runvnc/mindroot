import asyncio
import sys
from typing import Optional, Callable, Any, List, Dict, AsyncGenerator
COLORS = {'reset': '\x1b[0m', 'green': '\x1b[32m', 'yellow': '\x1b[33m', 'blue': '\x1b[34m', 'red': '\x1b[31m'}

async def read_stream(stream: asyncio.StreamReader, callback: Callable[[str], Any]):
    """Read from stream line by line and call the callback for each line."""
    while True:
        line = await stream.readline()
        if not line:
            break
        callback(line.decode('utf-8', errors='replace'))

async def run_command_with_streaming(cmd: List[str], stdout_callback: Callable[[str], Any], stderr_callback: Callable[[str], Any], cwd: Optional[str]=None, env: Optional[dict]=None) -> int:
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
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd, env=env)
        stdout_task = asyncio.create_task(read_stream(process.stdout, stdout_callback))
        stderr_task = asyncio.create_task(read_stream(process.stderr, stderr_callback))
        await asyncio.gather(stdout_task, stderr_task)
        exit_code = await process.wait()
        return exit_code
    except Exception as e:
        return 1

async def stream_command_as_events(cmd: List[str], cwd: Optional[str]=None, env: Optional[dict]=None) -> AsyncGenerator[Dict[str, str], None]:
    """Run a command and yield its output as events.
    
    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory for the command
        env: Environment variables for the command
        
    Yields:
        Events with type and data
    """
    yield {'event': 'message', 'data': f"Running command: {' '.join(cmd)}"}
    output_queue = asyncio.Queue()

    def stdout_callback(line):
        if line.strip():
            output_queue.put_nowait(('message', line.strip()))

    def stderr_callback(line):
        if line.strip():
            if 'WARNING:' in line or 'DEPRECATION:' in line or 'A new release of pip is available' in line:
                output_queue.put_nowait(('warning', line.strip()))
            else:
                output_queue.put_nowait(('warning', line.strip()))
    run_task = asyncio.create_task(run_command_with_streaming(cmd, stdout_callback, stderr_callback, cwd, env))
    while not run_task.done() or not output_queue.empty():
        try:
            event_type, data = await asyncio.wait_for(output_queue.get(), timeout=0.1)
            yield {'event': event_type, 'data': data}
        except asyncio.TimeoutError:
            await asyncio.sleep(0.01)
    exit_code = await run_task
    if exit_code == 0:
        yield {'event': 'complete', 'data': 'Command completed successfully'}
    else:
        yield {'event': 'error', 'data': f'Command failed with exit code {exit_code}'}