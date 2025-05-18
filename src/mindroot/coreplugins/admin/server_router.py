from fastapi import APIRouter, Response
import sys
import os
import psutil
import subprocess
import asyncio
import tempfile

router = APIRouter()

def get_start_method():
    try:
        current_process = psutil.Process()
        cmdline = current_process.cmdline()
        cmdline_str = ' '.join(cmdline).lower()
        
        print("Debug - Current process command line: ", cmdline)
        
        # Look for 'xingen' in our own command line
        if 'mindroot' in cmdline_str:
            # Check if we're under PM2 by environment or parent process tree
            if 'PM2_HOME' in os.environ or any('pm2' in p.name().lower() for p in current_process.parents()):
                return 'pm2'
            return 'mindroot'
            
        return 'unknown'
    except Exception as e:
        print(f"Debug - Error in get_start_method: {str(e)}")
        return 'unknown'

def spawn_restart():
    try:
        # Get the current command line that started this process
        current_process = psutil.Process()
        original_cmd = current_process.cmdline()
        
        # Create a temporary script file instead of using -c
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f"""
#!/usr/bin/env python3
# Temporary restart script for xingen
import time
import subprocess
import sys
import os

time.sleep(2.5)  # Wait for old server to fully shutdown

try:
    cmd = {original_cmd!r}
    print("Restarting mindroot with command:", cmd)
    subprocess.run(cmd, check=True)
except Exception as e:
    print(f"Error restarting mindroot: {{e}}")
    sys.exit(1)
finally:
    # Clean up this temporary script
    try:
        os.unlink(__file__)
    except:
        pass
""")
        
        script_path = f.name
        # Make the script executable
        os.chmod(script_path, 0o755)
        
        # Start detached process that will survive parent's exit
        subprocess.Popen(
            [sys.executable, script_path],
            start_new_session=True,
            # Let's keep stdout/stderr for debugging
            stdout=None,
            stderr=None
        )
        print(f"Debug - Spawned restart script: {script_path}")
        return True
    except Exception as e:
        print(f"Debug - Error in spawn_restart: {str(e)}")
        return False

async def delayed_exit():
    await asyncio.sleep(0.5)  # Wait 500ms to allow response to be sent
    sys.exit(0)

@router.post("/restart")
async def restart_server():
    try:
        method = get_start_method()
        
        if method == 'pm2':
            # PM2 will handle the restart automatically
            message = "Server stopping - PM2 will automatically restart it"
        elif method == 'mindroot':
            # Spawn process to restart server
            if spawn_restart():
                message = "Server stopping - restart process initiated"
            else:
                return {
                    "success": False,
                    "message": "Failed to initiate restart process",
                    "method": method
                }
        else:
            return {
                "success": False,
                "message": "Unknown start method - please restart server manually",
                "method": method
            }

        # Schedule the exit after response is sent
        asyncio.create_task(delayed_exit())
        
        return {
            "success": True,
            "message": message,
            "method": method
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Restart failed: {str(e)}",
            "method": method if 'method' in locals() else 'unknown'
        }

@router.post("/stop")
async def stop_server():
    try:
        method = get_start_method()
        if method == 'pm2':
            message = "Server stopping - PM2 will automatically restart it unless stopped through PM2"
        else:
            message = "Server stopping - manual restart will be required"

        # Schedule the exit after response is sent
        asyncio.create_task(delayed_exit())
            
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Stop failed: {str(e)}"
        }

@router.get("/ping")
async def ping():
    """Simple endpoint to check if server is running"""
    return {
        "status": "ok"
    }
