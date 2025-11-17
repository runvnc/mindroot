from lib.providers.hooks import hook
from lib.route_decorators import public_route, public_routes
from starlette.routing import Mount, Route
import json

@hook()
async def startup(app, context):

    def register_route(route_path, route_obj):
        """Helper function to register a route if it's marked as public"""
        if hasattr(route_obj, 'endpoint') and hasattr(route_obj.endpoint, '__public_route__'):
            public_routes.add(route_path)
            return True
        return False

    def process_routes(routes, path_prefix=''):
        """Recursively process routes and sub-routes"""
        for route in routes:
            if isinstance(route, Mount):
                mount_path = path_prefix + route.path.rstrip('/')
                if hasattr(route, 'routes'):
                    for sub_route in route.routes:
                        if isinstance(sub_route, Route):
                            full_path = mount_path + sub_route.path
            elif isinstance(route, Route):
                full_path = path_prefix + route.path
    process_routes(app.routes)