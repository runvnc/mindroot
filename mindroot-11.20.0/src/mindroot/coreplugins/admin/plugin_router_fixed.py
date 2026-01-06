from fastapi import APIRouter
from lib.route_decorators import requires_role

# Import the separate route modules
from .plugin_routes import router as plugin_routes
from .mcp_routes import router as mcp_routes
from .mcp_catalog_routes import router as mcp_catalog_routes
from .registry_settings_routes import router as registry_settings_routes
from .mcp_publish_routes import router as mcp_publish_routes
from .mcp_registry_routes import router as mcp_registry_routes

# Create main router with admin role requirement
router = APIRouter(
    dependencies=[requires_role('admin')]
)

# Include all the sub-routers
router.include_router(plugin_routes, tags=["plugins"])
router.include_router(mcp_routes, tags=["mcp"])
router.include_router(mcp_catalog_routes, tags=["mcp-catalog"])
router.include_router(registry_settings_routes, tags=["registry-settings"])
router.include_router(mcp_publish_routes, tags=["mcp-publish"])
router.include_router(mcp_registry_routes, tags=["mcp-registry"])