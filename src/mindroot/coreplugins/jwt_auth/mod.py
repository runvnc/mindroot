from lib.providers.hooks import hook
from lib.route_decorators import public_route, public_routes
from starlette.routing import Mount, Route
import json
print("---  Hello from JWT mod ---")

@hook()
async def startup(app, context):
    print('Running startup hook')
    print('Registering public routes:')
    
    def register_route(route_path, route_obj):
        """Helper function to register a route if it's marked as public"""
        if hasattr(route_obj, 'endpoint') and hasattr(route_obj.endpoint, '__public_route__'):
            print(f"Found public route: {route_path}")
            public_routes.add(route_path)
            return True
        return False
    
    def process_routes(routes, path_prefix=""):
        """Recursively process routes and sub-routes"""
        for route in routes:
            if isinstance(route, Mount):
                # Handle mounted sub-applications
                mount_path = path_prefix + route.path.rstrip('/')
                print(f"Processing mount: {mount_path}")
                
                # Process sub-routes within the mount
                if hasattr(route, 'routes'):
                    for sub_route in route.routes:
                        if isinstance(sub_route, Route):
                            full_path = mount_path + sub_route.path
                            if not register_route(full_path, sub_route):
                                print(f"Skipping private route: {full_path}")
                        else:
                            print(f"Skipping non-route in mount: {sub_route}")
                            
            elif isinstance(route, Route):
                # Handle direct routes
                full_path = path_prefix + route.path
                if not register_route(full_path, route):
                    print(f"Skipping private route: {full_path}")
            else:
                print(f"Skipping unknown route type: {route}")
    
    # Process all routes
    process_routes(app.routes)
    
    print(f"Final public routes registered: {public_routes}")
