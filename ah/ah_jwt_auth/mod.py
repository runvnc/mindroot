from ..hooks import hook, hook_manager
from ah.route_decorators import public_route
from starlette.routing import Mount

@hook()
async def startup(app, context):
    public_routes = set()
    for route in app.routes:
        print(route)
        print(dir(route))
        if isinstance(route, Mount):
            # Handle mounted routes
            for sub_route in route.routes:
                if hasattr(sub_route, 'endpoint') and hasattr(sub_route.endpoint, '__public_route__'):
                    public_routes.add(f"{route.path}{sub_route.path}")
        elif hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
            public_routes.add(route.path)
    
    # Store public_routes in the app state or context for later use
    app.state.public_routes = public_routes
