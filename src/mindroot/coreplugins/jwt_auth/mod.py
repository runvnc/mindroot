from lib.providers.hooks import hook
from lib.route_decorators import public_route, public_routes
from starlette.routing import Mount
import json
print("---  Hello from JWT mod ---")

@hook()
async def startup(app, context):
    print('Running startup hook')
    print('Registering public routes:')
    for route in app.routes: 
        print(route)
        if isinstance(route, Mount):
            for sub_route in route.routes:
                if hasattr(sub_route, 'endpoint') and hasattr(sub_route.endpoint, '__public_route__'):
                    print(f"Found public route: {route.path}{sub_route.path}")
                    public_routes.add(f"{route.path}{sub_route.path}")
                else:
                    print(f"Skipping private route: {route.path}{sub_route}")
        elif hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
            print(f"Found public route: {route.path}")
            public_routes.add(route.path)
        else:
            print(f"Skipping private route: {route}")


