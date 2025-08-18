import nanoid
import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from lib.plugins import list_enabled
from lib.templates import render
from .plugin_manager import router as plugin_manager_router
from lib.route_decorators import requires_role
from .mod import get_git_version_info

# Create separate routers for public and admin routes
public_router = APIRouter()  # No dependencies - for OAuth callbacks etc.
admin_router = APIRouter(dependencies=[requires_role('admin')])  # Admin only

# === PUBLIC ROUTES (no authentication required) ===
# Import and include the OAuth callback router in public router
from .oauth_callback_router import router as oauth_callback_router
public_router.include_router(oauth_callback_router)

# === ADMIN ROUTES (authentication required) ===
admin_router.include_router(plugin_manager_router, prefix="/plugin-manager", tags=["plugin-manager"])

@admin_router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render('admin', {"log_id": log_id})
    return html

@admin_router.get("/admin/model-preferences-v2", response_class=HTMLResponse)
async def get_model_preferences_v2_html():
    """Serve the new Model Preferences V2 page"""
    html = await render('model-preferences-v2', {})
    return html

@admin_router.post("/admin/get-version-info")
async def get_version_info():
    """Get version information, trying git first, then falling back to cached file."""
    try:
        # Get the path to this file to determine where to store version.txt
        current_file = Path(__file__)
        version_file = current_file.parent / "version.txt"
        
        # Try to get fresh git info using the command
        try:
            if get_git_version_info:
                git_info = await get_git_version_info()
                if git_info:
                    # Write to version.txt
                    with open(version_file, 'w') as f:
                        json.dump(git_info, f, indent=2)
                    return JSONResponse(git_info)
        except Exception as e:
            print(f"Failed to get git info: {e}")
        
        # Fall back to reading from version.txt
        if version_file.exists():
            with open(version_file, 'r') as f:
                cached_info = json.load(f)
                # Add note that this is cached
                cached_info['note'] = 'Cached version (git not available)'
                return JSONResponse(cached_info)
        
        # No version info available
        return JSONResponse({
            'commit_hash': 'Unknown',
            'commit_date': 'Unknown',
            'retrieved_at': 'Unknown',
            'note': 'Version information not available'
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting version info: {str(e)}")

from lib.logging.log_router import router as log_router
admin_router.include_router(log_router)

from .command_router import router as command_router
admin_router.include_router(command_router)

from .settings_router import router as settings_router
admin_router.include_router(settings_router)

# Use the fixed plugin router instead of the old one
from .plugin_router_fixed import router as plugin_router_fixed
admin_router.include_router(plugin_router_fixed, prefix="/admin", tags=["plugins", "mcp"])

# Keep the old plugin router for backward compatibility if needed
from .plugin_router import router as plugin_router
admin_router.include_router(plugin_router, prefix="/admin/legacy", tags=["legacy-plugins"])

from .persona_router import router as persona_router
admin_router.include_router(persona_router)

from .agent_router import router as agent_router
admin_router.include_router(agent_router)

from .server_router import router as server_router
admin_router.include_router(server_router, prefix="/admin/server", tags=["server"])

# Import and include the env_manager router
from coreplugins.env_manager.router import router as env_manager_router
admin_router.include_router(env_manager_router)

@admin_router.post("/admin/update-mindroot")
async def update_mindroot():
    """Update MindRoot using pip install --upgrade mindroot"""
    import subprocess
    import sys
    
    try:
        # Run pip install --upgrade mindroot in the current environment
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "mindroot"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return JSONResponse({
                "success": True,
                "message": "MindRoot updated successfully",
                "output": result.stdout,
                "note": "Restart the application to use the updated version"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Failed to update MindRoot",
                "error": result.stderr,
                "output": result.stdout
            })
            
    except subprocess.TimeoutExpired:
        return JSONResponse({
            "success": False,
            "message": "Update timed out after 5 minutes",
            "error": "Process timed out"
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": "Error during update",
            "error": str(e)
        })

# === MAIN ROUTER COMBINING PUBLIC AND ADMIN ===
# Create main router that combines both public and admin routes
router = APIRouter()
router.include_router(public_router)  # Public routes first (no auth)
router.include_router(admin_router)   # Admin routes (with auth)
