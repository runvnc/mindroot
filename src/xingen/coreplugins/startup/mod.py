from lib.providers.hooks import hook, hook_manager
from lib.route_decorators import public_route, public_routes
from starlette.routing import Mount
import termcolor

print("--- AH Startup ---")

async def on_load(app):
    print(termcolor.colored("startup plugin calling startup() hook...", 'yellow', 'on_green'))
    await hook_manager.startup(app, context=None)

