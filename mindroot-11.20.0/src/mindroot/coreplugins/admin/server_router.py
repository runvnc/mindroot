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
        if 'mindroot' in cmdline_str:
            if 'PM2_HOME' in os.environ or any(('pm2' in p.name().lower() for p in current_process.parents())):
                return 'pm2'
            return 'mindroot'
        return 'unknown'
    except Exception as e:
        return 'unknown'

def spawn_restart():
    try:
        current_process = psutil.Process()
        original_cmd = current_process.cmdline()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(f'\n#!/usr/bin/env python3\n# Temporary restart script for xingen\nimport time\nimport subprocess\nimport sys\nimport os\n\ntime.sleep(2.5)  # Wait for old server to fully shutdown\n\ntry:\n    cmd = {original_cmd!r}\n    print("Restarting mindroot with command:", cmd)\n    subprocess.run(cmd, check=True)\nexcept Exception as e:\n    print(f"Error restarting mindroot: {{e}}")\n    sys.exit(1)\nfinally:\n    # Clean up this temporary script\n    try:\n        os.unlink(__file__)\n    except:\n        pass\n')
        script_path = f.name
        os.chmod(script_path, 493)
        subprocess.Popen([sys.executable, script_path], start_new_session=True, stdout=None, stderr=None)
        return True
    except Exception as e:
        return False

async def delayed_exit():
    await asyncio.sleep(0.5)
    sys.exit(0)

@router.post('/restart')
async def restart_server():
    try:
        method = get_start_method()
        if method == 'pm2':
            message = 'Server stopping - PM2 will automatically restart it'
        elif method == 'mindroot':
            if spawn_restart():
                message = 'Server stopping - restart process initiated'
            else:
                return {'success': False, 'message': 'Failed to initiate restart process', 'method': method}
        else:
            return {'success': False, 'message': 'Unknown start method - please restart server manually', 'method': method}
        asyncio.create_task(delayed_exit())
        return {'success': True, 'message': message, 'method': method}
    except Exception as e:
        return {'success': False, 'message': f'Restart failed: {str(e)}', 'method': method if 'method' in locals() else 'unknown'}

@router.post('/stop')
async def stop_server():
    try:
        method = get_start_method()
        if method == 'pm2':
            message = 'Server stopping - PM2 will automatically restart it unless stopped through PM2'
        else:
            message = 'Server stopping - manual restart will be required'
        asyncio.create_task(delayed_exit())
        return {'success': True, 'message': message}
    except Exception as e:
        return {'success': False, 'message': f'Stop failed: {str(e)}'}

@router.get('/ping')
async def ping():
    """Simple endpoint to check if server is running"""
    return {'status': 'ok'}