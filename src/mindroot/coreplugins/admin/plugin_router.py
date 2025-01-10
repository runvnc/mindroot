from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from lib.route_decorators import requires_role
from lib import plugins

router = APIRouter()

class PluginUpdateRequest(BaseModel):
    plugins: dict

@requires_role('admin')
@router.post("/update-plugins")
def update_plugins(request: PluginUpdateRequest):
    try:
        with open('plugins.json', 'r') as file:
            plugins_data = json.load(file)

        for plugin in plugins_data:
            if plugin['name'] in request.plugins:
                plugin['enabled'] = request.plugins[plugin['name']]

        with open('plugins.json', 'w') as file:
            json.dump(plugins_data, file, indent=2)

        plugins.load('plugin_manifest.json')

        return {"message": "Plugins updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@requires_role('admin')
@router.get("/get-plugins")
async def get_plugins():
    try:
        return plugins.load_plugin_manifest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

