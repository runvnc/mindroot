from lib.providers.hooks import hook, hook_manager
from lib.route_decorators import public_route, public_routes
from starlette.routing import Mount
import termcolor
import os

print("--- AH Startup ---")

async def on_load(app):
    print(termcolor.colored("startup plugin calling startup() hook...", 'yellow', 'on_green'))

    for dirs in ['data/context', 'data/chat']:
        os.makedirs(dirs, exist_ok=True)

    context = { "startup_dir": os.getcwd() }
    await hook_manager.startup(app, context=context)

