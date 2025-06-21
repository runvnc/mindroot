import nanoid
import os
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from lib.plugins import list_enabled
from lib.templates import render
from .plugin_manager import router as plugin_manager_router
from lib.route_decorators import requires_role
from .mod import get_git_version_info


# Create admin router with role requirement for all routes under it
router = APIRouter(
    dependencies=[requires_role('admin')]
)

router.include_router(plugin_manager_router, prefix="/plugin-manager", tags=["plugin-manager"])

@router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render('admin', {"log_id": log_id})
    return html

@router.post("/admin/get-version-info")
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
router.include_router(log_router)

from .command_router import router as command_router
router.include_router(command_router)

from .settings_router import router as settings_router
router.include_router(settings_router)

from .plugin_router import router as plugin_router
router.include_router(plugin_router)

from .persona_router import router as persona_router
router.include_router(persona_router)

from .agent_router import router as agent_router
router.include_router(agent_router)

from .server_router import router as server_router
router.include_router(server_router, prefix="/admin/server", tags=["server"])

# Import and include the env_manager router
from coreplugins.env_manager.router import router as env_manager_router
router.include_router(env_manager_router)
