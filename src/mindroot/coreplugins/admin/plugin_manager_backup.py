from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import traceback
import os
import json
from typing import List, Optional
from lib.plugins import (
    load_plugin_manifest, update_plugin_manifest, plugin_install,
    save_plugin_manifest, plugin_update, toggle_plugin_state, get_plugin_path
)
import asyncio


router = APIRouter()

class DirectoryRequest(BaseModel):
    directory: str

class PluginRequest(BaseModel):
    plugin: str

class GitHubPluginRequest(BaseModel):
    plugin: str
    url: Optional[str] = None
    github_url: Optional[str] = None

class TogglePluginRequest(BaseModel):
    plugin: str
    enabled: bool

class InstallFromIndexRequest(BaseModel):
    plugin: str
    index_name: str

class StreamInstallRequest(BaseModel):
    plugin: str
    source: str
    source_path: str = None


class PluginMetadata(BaseModel):
    description: Optional[str] = None
    commands: Optional[List[str]] = None
    services: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None

import sys, fcntl, os, shlex, queue, subprocess as sp


# Simple approach to capture output in real-time
async def run_command_with_output(cmd, queue):
    """Run a command and capture output in real-time."""
    print(f"Running command: {cmd}")
    
    # Start the process
    process = sp.Popen(
        cmd,
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Helper function to read from a pipe and put lines in the queue
    async def read_pipe(pipe, is_stderr=False):
        for line in iter(pipe.readline, ''):
            if not line:  # Empty line means EOF
                break
            line = line.strip()
            if line:
                if is_stderr:
                    if "A new release of pip is available" in line or line.startswith("WARNING:"):
                        await queue.put(("warning", line))
                    else:
                        await queue.put(("error", line))
                else:
                    await queue.put(("message", line))
            await asyncio.sleep(0.01)  # Small delay to allow other tasks to run
    
    # Create tasks to read from stdout and stderr
    stdout_task = asyncio.create_task(read_pipe(process.stdout))
    stderr_task = asyncio.create_task(read_pipe(process.stderr, True))
    
    # Wait for the process to complete
    return_code = await asyncio.get_event_loop().run_in_executor(None, process.wait)
    
    # Wait for the reading tasks to complete
    await stdout_task
    await stderr_task
    
    # Close the pipes
    process.stdout.close()
    process.stderr.close()
    
    # Return the return code
    return return_code


# Generator for SSE events
async def stream_command_output(cmd, message):
    """Stream command output as SSE events."""
    # Send initial message
    yield {"event": "message", "data": message}
    
    # Create a queue for output
    output_queue = asyncio.Queue()
    
    # Run the command and capture output
    return_code = await run_command_with_output(cmd, output_queue)
    
    # Stream output from the queue
    while not output_queue.empty():
        event_type, data = await output_queue.get()
        yield {"event": event_type, "data": data}
    
    # Send completion message
    if return_code == 0:
        yield {"event": "complete", "data": "Installation completed successfully"}
    else:
        yield {"event": "error", "data": "Installation failed"}

import sys, io, subprocess


async def stream_install_generator(plugin_name, source, source_path=None, remote_source=None):
    """Generator for streaming plugin installation output."""
    # Create a subprocess to capture output
    import subprocess
    import sys
    import io
    from contextlib import redirect_stdout, redirect_stderr
    import threading, select
    
    # Send initial message
    yield {"event": "message", "data": f"Starting installation of {plugin_name} from {source}..."}
    
    # Create string buffers to capture output
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    output_queue = []
    installation_complete = threading.Event()
    installation_success = [False]  # Use a list to make it mutable in the inner function
    import time, fcntl, os, shlex, queue, subprocess as sp

    # Helper function to read from pipes without blocking
    def read_pipes_nonblocking(process):
        stdout_data = []
        stderr_data = []
        
        # Set pipes to non-blocking mode
        if not process.stdout or not process.stderr:
            return stdout_data, stderr_data
        
        
        # Set stdout to non-blocking
        stdout_fd = process.stdout.fileno()
        fl = fcntl.fcntl(stdout_fd, fcntl.F_GETFL)
        fcntl.fcntl(stdout_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # Set stderr to non-blocking
        stderr_fd = process.stderr.fileno()
        fl = fcntl.fcntl(stderr_fd, fcntl.F_GETFL)
        fcntl.fcntl(stderr_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # Read from pipes
        try:
            readable, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)
        except (ValueError, select.error):
            return stdout_data, stderr_data
        
        if process.stdout in readable:
            try:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    stdout_data.append(stdout_line.strip())
            except IOError:
                pass
        
        if process.stderr in readable:
            try:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    stderr_data.append(stderr_line.strip())
            except IOError:
                pass
                
        return stdout_data, stderr_data
    
    # Helper function to determine if a stderr line is an actual error or just a warning/notice
    def is_actual_error(line):
        # Pip upgrade notices are not actual errors
        if "A new release of pip is available" in line:
            return False
        if "pip is being invoked by an old script wrapper" in line:
            return False
        # Add other known non-error stderr messages here
        if line.startswith("WARNING:") or line.startswith("DEPRECATION:"):
            return False
        # Consider everything else as an error
        return True
    
    # Capture output directly using subprocess.check_output
    # Thread function to continuously read from a pipe
    def reader_thread(pipe, queue, is_stderr=False, stderr_lines=None):
        try:
            with pipe:
                for line in iter(pipe.readline, ''):
                    if not line:  # Empty line means EOF
                        break
                    line = line.strip()
                    if is_stderr:
                        # Always add stderr lines to the all_stderr_lines list
                        if stderr_lines is not None:
                            stderr_lines.append(line)
                        
                        if is_actual_error(line):
                            print(f"ERROR LINE: {line}")  # Debug
                            queue.put(("error", line))
                        else:
                            print(f"WARNING LINE: {line}")  # Debug
                            queue.put(("warning", line))
                    else:
                        queue.put(("message", line))
        except Exception as e:
            queue.put(("error", f"Error reading from {'stderr' if is_stderr else 'stdout'}: {str(e)}"))
        finally:
            if is_stderr:
                queue.put(("reader_done", "stderr"))
            else:
                queue.put(("reader_done", "stdout"))
    
    # Helper function to check if a line contains meaningful output
    def is_meaningful_output(line):
        return bool(line and line.strip() and not line.isspace())
    
    # Helper function to run a pip command and capture output
    def run_pip_command(cmd, message):
        output_queue.append(("message", message))
        
        all_stderr_lines = []
        
        # Make all_stderr_lines accessible to the reader_thread function
        # Use shell=True for better output capture on some systems
        if isinstance(cmd, list):
            cmd_str = ' '.join(shlex.quote(str(arg)) for arg in cmd)
        else:
            cmd_str = cmd
            
        process = subprocess.Popen(
            # Use shell=True to get more verbose output
            cmd_str,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True,
            bufsize=1  # Line buffered
        )
        
        output_queue.append(("message", f"Running: {cmd_str}"))

        # Create a queue for thread communication
        q = queue.Queue()
        
        # Start reader threads
        stdout_thread = threading.Thread(target=reader_thread, args=(process.stdout, q, False, None))
        stderr_thread = threading.Thread(target=reader_thread, args=(process.stderr, q, True, all_stderr_lines))
        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()
        
        # Track which readers are done
        readers_done = set()
        
        # Read output in real-time using non-blocking approach
        # Process queue items until both readers are done and process has exited
        while len(readers_done) < 2 or process.poll() is None:
            try:
                item_type, item = q.get(timeout=0.1)
                
                if item_type == "reader_done":
                    readers_done.add(item)  # item will be "stdout" or "stderr"
                elif item_type == "error":
                    all_stderr_lines.append(item)
                    output_queue.append(("error", item))
                    # Send error event
                    yield {"event": "error", "data": item}
                elif item_type == "warning":
                    all_stderr_lines.append(item)
                    output_queue.append(("warning", item))
                    # Send warning event
                    yield {"event": "warning", "data": item}
                else:  # message
                    if is_meaningful_output(item):
                        output_queue.append(("message", item))
                        # Send message event
                        yield {"event": "message", "data": item}
                
                q.task_done()
            except queue.Empty:
                # No output available, just continue
                pass
        
        # Wait for threads to finish
        stdout_thread.join()
        stderr_thread.join()
            
        # If the process failed but only had warnings (not actual errors), consider it a success
        if process.returncode != 0:
            # Debug
            print(f"All stderr lines: {all_stderr_lines}")
            print(f"Output queue: {output_queue}")
            
            # Check if there were any actual errors in stderr
            has_actual_errors = any(is_actual_error(line) for line in all_stderr_lines)
            print(f"Process returned {process.returncode}, has_actual_errors={has_actual_errors}")
            
            # If no actual errors, consider it a success
            if not has_actual_errors:
                return 0
        
        # Add a final message with the return code
        output_queue.append(("message", f"Process completed with return code: {process.returncode}"))
        yield {"event": "message", "data": f"Process completed with return code: {process.returncode}"}
        
        success_status = process.returncode == 0 or not any(is_actual_error(line) for line in all_stderr_lines)
        
        # Add a final success/error message
        if success_status:
            yield {"event": "complete", "data": "Installation completed successfully"}
        else:  
            yield {"event": "error", "data": "Installation failed"}
        
        # Return the process return code
        return process.returncode
    
    # Function to run pip install and capture output
    def run_pip_install():
        try:
            if source == 'github':
                # First download the GitHub repo
                output_queue.append(("message", f"Downloading GitHub repository {source_path}..."))
                
                # Install from GitHub
                cmd = [sys.executable, '-m', 'pip', 'install', '-e', f"{source_path}", '-v']
                return_code = run_pip_command(cmd, f"Installing {plugin_name} from GitHub repository {source_path}...")
                installation_success[0] = (return_code == 0)
                
            elif source == 'local':
                # Run pip install for local source
                cmd = [sys.executable, '-m', 'pip', 'install', '-e', source_path, '-v']
                return_code = run_pip_command(cmd, f"Installing from local path: {source_path}")
                installation_success[0] = (return_code == 0)
                print(f"Local installation result: return_code={return_code}, success={installation_success[0]}")
            elif source == 'pypi':
                # Run pip install for PyPI package
                cmd = [sys.executable, '-m', 'pip', 'install', plugin_name, '-v']
                return_code = run_pip_command(cmd, f"Installing from PyPI: {plugin_name}")
                installation_success[0] = (return_code == 0)
                print(f"PyPI installation result: return_code={return_code}, success={installation_success[0]}")
            installation_complete.set()
        except Exception as e:
            trace = traceback.format_exc()
            output_queue.append(("error", f"Error installing plugin: {str(e)}"))
            for line in trace.splitlines():
                output_queue.append(("error", line))
            installation_complete.set()
    
    try:
        # Start the installation process
        thread = threading.Thread(target=run_pip_install)
        thread.start()
        
        # Stream output from the queue while waiting for installation to complete
        while not installation_complete.is_set() or output_queue:
            if output_queue:
                event_type, data = output_queue.pop(0)
                yield {"event": event_type, "data": data}
            else:
                await asyncio.sleep(0.1)
        
        # Send completion message
        if installation_success[0]:
            yield {"event": "complete", "data": f"Plugin {plugin_name} installed successfully"}
        else:
            yield {"event": "error", "data": f"Failed to install plugin {plugin_name}"}
    
    except Exception as e:
        trace = traceback.format_exc()
        yield {"event": "error", "data": f"Error installing plugin: {str(e)}"}
        for line in trace.splitlines():
            yield {"event": "error", "data": line}

@router.post("/stream-install-plugin", response_class=EventSourceResponse)
async def stream_install_plugin(request: StreamInstallRequest):
    """Stream the installation process of a plugin using SSE."""
    return EventSourceResponse(stream_install_generator(
        request.plugin, request.source, request.source_path))

@router.get("/stream-install-plugin", response_class=EventSourceResponse)
async def stream_install_plugin_get(request: Request):
    """Stream the installation process of a plugin using SSE (GET method)."""
    # Extract parameters from query string
    plugin = request.query_params.get("plugin", "")
    source = request.query_params.get("source", "")
    source_path = request.query_params.get("source_path", "")
    
    # Use the new simpler approach
    if source == 'github':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', source_path, '-v']
        message = f"Installing {plugin} from GitHub repository {source_path}..."
    elif source == 'local':
        cmd = [sys.executable, '-m', 'pip', 'install', '-e', source_path, '-v']
        message = f"Installing from local path: {source_path}"
    elif source == 'pypi':
        cmd = [sys.executable, '-m', 'pip', 'install', plugin, '-v']
        message = f"Installing from PyPI: {plugin}"
    else:
        return {"success": False, "message": "Invalid source"}
    
    # Return SSE response
    return EventSourceResponse(stream_command_output(cmd, message))

@router.get("/get-all-plugins")
async def get_all_plugins():
    try:
        manifest = load_plugin_manifest()
        plugins = []
        
        # Process core plugins
        for plugin_name, plugin_info in manifest['plugins']['core'].items():
            plugins.append({
                "name": plugin_name,
                "category": "core",
                "enabled": plugin_info['enabled'],
                "source": "core",
                "remote_source": plugin_name,
                "version": "1.0.0",
                "description": plugin_info.get('metadata', {}).get('description', '')
            })

        # Process installed plugins
        for plugin_name, plugin_info in manifest['plugins']['installed'].items():
            plugins.append({
                "name": plugin_name,
                "category": "installed",
                "enabled": plugin_info['enabled'],
                "source": plugin_info['source'],
                "remote_source": plugin_info.get('remote_source', plugin_info.get('github_url')),
                "source_path": plugin_info.get('source_path'),
                "version": plugin_info.get('version', '0.0.1'),
                "description": plugin_info.get('metadata', {}).get('description', ''),
                "index_source": plugin_info.get('metadata', {}).get('index_source')
            })

        return {"success": True, "data": plugins}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error fetching plugins: {str(e)}\n\n{trace}"}


@router.post("/scan-directory")
async def scan_directory(request: DirectoryRequest):
    try:
        directory = request.directory
        if not os.path.isdir(directory):
            return {"success": False, "message": "Invalid directory path"}
        
        discovered_plugins = discover_plugins(directory)
        manifest = load_plugin_manifest()
        print("discoverd_plugins", discovered_plugins)
        # Update installed plugins from discovered ones
        for plugin_name, plugin_info in discovered_plugins.items():
            plugin_info['source'] = 'local'
            plugin_info['metadata'] = plugin_info.get('metadata', {}) or {
                "description": plugin_info.get('description', ''),
                "install_date": plugin_info.get('install_date', ''),
                "commands": plugin_info.get('commands', []),
                "services": plugin_info.get('services', [])
            }
            print(plugin_info)
            manifest['plugins']['installed'][plugin_name] = plugin_info

        # Prepare plugin list for response
        plugins_list = [{
            "name": name,
            "description": info.get('metadata', {}).get('description', info.get('description', ''))
        } for name, info in discovered_plugins.items()]
        
        save_plugin_manifest(manifest)
        return {"success": True, 
                "message": f"Scanned {len(discovered_plugins)} plugins in {directory}",
                "plugins": plugins_list}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error during scan: {str(e)}\n\n{trace}"}

@router.post("/install-local-plugin")
async def install_local_plugin(request: PluginRequest):
    try:
        plugin_name = request.plugin
        plugin_path = get_plugin_path(plugin_name)
        
        if not plugin_path:
            return {"success": False, "message": "Plugin path not found"}
        
        success = await plugin_install(plugin_name, source='local', source_path=plugin_path)
        if success:
            return {"success": True, "message": f"Plugin {plugin_name} installed successfully"}
        else:
            return {"success": False, "message": "Installation failed"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing plugin: {str(e)}\n\n{trace}"}


@router.post("/install-x-github-plugin")
async def install_github_plugin(request: GitHubPluginRequest):
    try:
        print("Request:", request)
        url = request.url or request.github_url
        success = await plugin_install('test', source='github', source_path=url)
        if success:
            return {"success": True, "message": "Plugin installed successfully from GitHub"}
        else:
            return {"success": False, "message": "Installation failed"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing from GitHub: {str(e)}\n\n{trace}"}

@router.post("/install-from-index")
async def install_from_index(request: InstallFromIndexRequest):
    try:
        # Load the index to get plugin information
        index_path = os.path.join('indices', f"{request.index_name}.json")
        if not os.path.exists(index_path):
            return {"success": False, "message": "Index not found"}

        with open(index_path, 'r') as f:
            index_data = json.load(f)

        # Find plugin in index
        plugin_data = None
        for plugin in index_data.get('plugins', []):
            if plugin['name'] == request.plugin:
                plugin_data = plugin
                break

        if not plugin_data:
            return {"success": False, "message": "Plugin not found in index"}

        # Install the plugin
        if plugin_data.get('github_url'):
            success = await plugin_install(
                request.plugin,
                source='github',
                source_path=plugin_data['github_url']
            )
        elif plugin_data.get('source_path'):
            success = await plugin_install(
                request.plugin,
                source='local',
                source_path=plugin_data['source_path']
            )
        else:
            return {"success": False, "message": "No valid installation source in index"}

        if success:
            # Update plugin metadata with index information
            manifest = load_plugin_manifest()
            if request.plugin in manifest['plugins']['installed']:
                manifest['plugins']['installed'][request.plugin]['metadata']['index_source'] = request.index_name
                save_plugin_manifest(manifest)

            return {"success": True, "message": f"Plugin {request.plugin} installed successfully from index"}
        else:
            return {"success": False, "message": "Installation failed"}

    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error installing from index: {str(e)}\n\n{trace}"}


@router.post("/toggle-plugin")
async def toggle_plugin(request: TogglePluginRequest):
    try:
        success = toggle_plugin_state(request.plugin, request.enabled)
        if success:
            return {"success": True, "message": f"Plugin {request.plugin} {'enabled' if request.enabled else 'disabled'} successfully"}
        else:
            return {"success": False, "message": "Failed to toggle plugin state"}
    except Exception as e:
        trace = traceback.format_exc()
        return {"success": False, "message": f"Error toggling plugin: {str(e)}\n\n{trace}"}

# Helper function
def discover_plugins(directory):
    discovered = {}
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        plugin_info_path = os.path.join(item_path, 'plugin_info.json')
        
        if os.path.isfile(plugin_info_path):
            try:
                with open(plugin_info_path, 'r') as f:
                    plugin_info = json.load(f)
                plugin_info['enabled'] = False
                plugin_info['source_path'] = item_path
                discovered[plugin_info['name']] = plugin_info
            except json.JSONDecodeError:
                print(f"Error reading plugin info for {item}")
                continue

    return discovered
