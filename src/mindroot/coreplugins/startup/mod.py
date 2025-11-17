from lib.providers.hooks import hook, hook_manager
from lib.route_decorators import public_route, public_routes
from lib.chatcontext import ChatContext
from starlette.routing import Mount
import termcolor
import os

async def on_load(app):
    context_dir = os.environ.get('CHATCONTEXT_DIR', 'data/context')
    chatlog_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
    for dirs in [context_dir, chatlog_dir]:
        os.makedirs(dirs, exist_ok=True)
    context = ChatContext(user='startup')
    context.app = app
    await hook_manager.startup(app, context=context)