import nanoid
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from lib.plugins import list_enabled
from lib.templates import render
from .plugin_manager import router as plugin_manager_router
from lib.route_decorators import requires_role

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


