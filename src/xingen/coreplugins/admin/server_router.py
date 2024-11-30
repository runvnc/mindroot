from fastapi import APIRouter
import sys
import os
import psutil
import subprocess
import asyncio

router = APIRouter()

def get_start_method():
    try:
        current_process = psutil.Process()
        cmdline = current_process.cmdline()
        cmdline_str = ' '.join(cmdline).lower()
        
        print("Debug - Current process command line: ", cmdline)
        
        # Look for 'xingen' in our own command line
        if 'xingen' in cmdline_str:
            # Check if we're under PM2 by environment or parent process tree
            if 'PM2_HOME' in os.environ or any('pm2' in p.name().lower() for p in current_process.parents()):
                return 'pm2'
            return 'xingen'
            
        return 'unknown'
    except Exception as e:
        print(f"Debug - Error in get_start_method: {str(e)}")
        return 'unknown'

def spawn_restart():
    try:
        # Get the current command line that started this process
        current_process = psutil.Process()
        original_cmd = current_process.cmdline()
        
        # Script to wait briefly then restart using the same command
        script = f"""
import time
import subprocess
import sys

time.sleep(2)  # Wait for old server to fully shutdown
try:
    cmd = {original_cmd}
    subprocess.run(cmd, check=True)
except subprocess.CalledProcessError:
    sys.exit(1)
"""
        # Start detached process that will survive parent's exit
        subprocess.Popen(
            [sys.executable, '-c', script],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
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
        elif method == 'xingen':
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