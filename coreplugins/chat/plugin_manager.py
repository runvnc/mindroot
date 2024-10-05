from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from lib.plugins import (
    load_plugin_manifest,
    plugin_install,
    plugin_update,
    toggle_plugin_state,
    list_enabled
)

router = APIRouter()

# Request Models
class PluginInstallRequest(BaseModel):
    plugin_name: str
    source: str = 'local'
    source_path: str = None

class PluginToggleRequest(BaseModel):
    plugin_name: str
    enabled: bool

class PluginRequest(BaseModel):
    plugin: str

# API Endpoints

@router.post("/install-plugin")
async def install_plugin(request: PluginInstallRequest):
    try:
        success = plugin_install(request.plugin_name, source=request.source, source_path=request.source_path)
        if success:
            return {"message": f"Plugin {request.plugin_name} installed successfully."}
        else:
            raise HTTPException(status_code=500, detail="Plugin installation failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-plugin")
async def update_plugin(request: PluginRequest):
    try:
        success = plugin_update(request.plugin)
        if success:
            return {"message": f"Plugin {request.plugin} updated successfully."}
        else:
            raise HTTPException(status_code=500, detail="Plugin update failed.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle-plugin")
async def toggle_plugin(request: PluginToggleRequest):
    try:
        success = toggle_plugin_state(request.plugin_name, request.enabled)
        if success:
            state = 'enabled' if request.enabled else 'disabled'
            return {"message": f"Plugin {request.plugin_name} {state} successfully."}
        else:
            raise HTTPException(status_code=500, detail="Failed to toggle plugin state.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get-all-plugins")
async def get_all_plugins():
    try:
        manifest = load_plugin_manifest()
        plugins_list = []
        for category in manifest['plugins']:
            for plugin_name, plugin_info in manifest['plugins'][category].items():
                plugins_list.append({
                    'name': plugin_name,
                    'category': category,
                    'enabled': plugin_info.get('enabled', False),
                    'source': plugin_info.get('source'),
                    'source_path': plugin_info.get('source_path')
                })
        return plugins_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
