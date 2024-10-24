from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from lib.plugin_manager import router as plugin_manager_router

router = APIRouter()

router.include_router(plugin_manager_router, prefix="/plugin-manager", tags=["plugin-manager"])

@router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render('admin', {"log_id": log_id})
    return html


from .lib.logging.log_router import router as log_router
app.include_router(log_router)

from .lib.routers.settings_router import router as settings_router
app.include_router(settings_router)

from .lib.routers.plugin_router import router as plugin_router
app.include_router(plugin_router)

from .lib.routers.persona_router import router as persona_router
app.include_router(persona_router)

from .lib.routers.agent_router import router as agent_router
app.include_router(agent_router)


