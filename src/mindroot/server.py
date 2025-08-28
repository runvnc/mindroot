from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from .lib import plugins
from .lib.chatcontext import ChatContext
from .lib.providers.hooks import hook_manager
from .lib.utils.debug import debug_box
import asyncio
import sys
import uvicorn
from termcolor import colored
import socket
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .lib.cli.plugins import install_plugins_from_cli
from dotenv import load_dotenv
from .migrate import run_migrations

# import for file copy
from shutil import copyfile

# Load environment variables from .env file at the start
# Set override=True to make .env variables override existing environment variables
load_dotenv(override=True)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Run the MindRoot server or manage plugins.", allow_abbrev=False)

    # Server arguments are top-level
    parser.add_argument("-p", "--port", type=int, help="Port to run the server on")
    parser.add_argument("-u", "--admin-user", type=str, help="Admin username")
    parser.add_argument("-pw", "--admin-password", type=str, help="Admin password")

    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    # Explicit 'server' command for clarity in help, but it's the default action
    server_parser = subparsers.add_parser('server', help='Run the web server (default action)')

    # Plugin command group
    plugin_parser = subparsers.add_parser('plugin', help='Manage plugins')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_command', required=True)
    install_parser = plugin_subparsers.add_parser('install', help='Install or update one or more plugins')
    install_parser.add_argument('plugins', nargs='+', help='List of plugins to install (e.g., runvnc/plugin-name)')
    install_parser.add_argument('--reinstall', action='store_true', help='Force reinstall of the plugin if it already exists.')

    return parser.parse_args()

def get_project_root():
    return Path(os.getcwd())
    #return Path(__file__).parent

def create_directories():
    root = get_project_root()
    directories = [
        "data",
        "imgs",
        "models",
        "models/face",
        "models/llm",
        "static/personas",
        "personas",
        "personas/local",
        "personas/shared",
        "data/sessions"
    ]
    chatlog_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
    directories.append(chatlog_dir)

    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

create_directories()

import mimetypes
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

templates = None
app = None
failed_plugins = []

async def setup_app_internal(app_):
    global app, templates
    app = app_
    
    root = get_project_root()
    source_root = Path(__file__).parent
    await plugins.load(app=app)
    app.mount("/static", StaticFiles(directory=str(root / "static"), follow_symlink=True), name="static")
    app.mount("/imags", StaticFiles(directory=str(root / "imgs"), follow_symlink=True), name="imgs")

    if not os.path.exists(root / "imgs/logo.png"):
        print(colored("No logo found, copying default logo from coreplugins", "yellow"))
        copyfile(str(source_root / "coreplugins/home/static/imgs/logo.png"), str(root / "imgs/logo.png"))
    # if docs are not in the root, copy them from source_root 
    if not os.path.exists(root / "docs/_build/index.html"):
        print(colored("No manual found, copying default manual from coreplugins", "yellow"))
        import shutil
        shutil.copytree(str(source_root / "docs/_build/html"), str(root / "manual"), dirs_exist_ok=True)
    # now mount the manual from root
    if os.environ.get('MR_HIDE_DOCS', 'false').lower() != 'true':
        app.mount("/manual", StaticFiles(directory=str(root / "manual"), follow_symlink=True), name="manual")
    return app

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except socket.error:
            return True

def find_available_port(start_port=8010, max_attempts=100):
    port = start_port
    while port < start_port + max_attempts:
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"Could not find an available port after {max_attempts} attempts")

class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # First get the response from other middleware and routes
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"

        #chat widgets don't work if we do this
        if os.environ.get('MR_X_FRAME_SAMEORIGIN', 'false').lower() == 'true':
            response.headers["X-Frame-Options"] = "SAMEORIGIN"

        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

def main():
    global app
    
    # Run migrations first, before anything else
    run_migrations()

    args = parse_args()

    # If the command is 'plugin', handle it and exit.
    if args.command == 'plugin':
        if args.plugin_command == 'install':
            asyncio.run(install_plugins_from_cli(args.plugins, reinstall=args.reinstall))
        sys.exit(0)

    # Default action: run the server. The server arguments are on the main 'args' object.
    cmd_args = args
    port = 8010
    if cmd_args.port:
        port = cmd_args.port
    else:
        cmd_args.port = port

    app = FastAPI()

    app.state.cmd_args = cmd_args

    debug_box("pre_load")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(plugins.pre_load(app)) # middleware

    debug_box("finished with pre_load, now calling uvicorn.run")

    @app.on_event("startup")
    async def setup_app():
        global app
        await setup_app_internal(app)
        print(colored("Plugin setup complete", "green"))

    @app.on_event("shutdown")
    async def shutdown_event():
        print("Shutting down MindRoot")
        hook_manager.eject()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Replace with your specific origins for production
        allow_credentials=True,
        allow_methods=["*"],  # Or specify: ["GET", "POST", "PUT", "DELETE", etc.]
        allow_headers=["*"],  # Or specify required headers
        expose_headers=["*"]  # Headers that browsers are allowed to access
    )

    app.add_middleware(HeaderMiddleware)

    try:
        print(colored(f"Starting server on port {port}", "green"))
        uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on", timeout_graceful_shutdown=2)
    except Exception as e:
        print(colored(f"Error starting server: {str(e)}", "red"))

if __name__ == "__main__":
    main()
