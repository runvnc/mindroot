from ..hooks import hook, hook_manager
from ah.route_decorators import public_route

@hook()
async def startup(app, context):
    for route in app.routes:
        print(route)
        print(dir(route))
        if hasattr(route.endpoint, '__public_route__'):
            public_routes.add(route.path)
