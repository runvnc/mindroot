import os
import logging

# Check MR_DEBUG env variable
MR_DEBUG = os.environ.get('MR_DEBUG', '').lower() in ('1', 'true', 'yes')

# Set root logger level based on MR_DEBUG
if MR_DEBUG:
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    # Disable most logging to reduce overhead
    logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

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
from pyinstrument import Profiler
from datetime import datetime

# Load environment variables from .env file at the start
# Set override=True to make .env variables override existing environment variables
load_dotenv(override=True)

# Patch os.environ to check context.env for per-session overrides
from .lib.context_environ import patch_environ  # Auto-patches on import

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

    # User command group
    user_parser = subparsers.add_parser('user', help='Manage users')
    user_subparsers = user_parser.add_subparsers(dest='user_command', required=True)
    create_user_parser = user_subparsers.add_parser('create', help='Create a new user')
    create_user_parser.add_argument('username', type=str, help='Username')
    create_user_parser.add_argument('email', type=str, help='Email address')
    create_user_parser.add_argument('--password', type=str, default=None, help='Password (auto-generated if not provided)')
    create_user_parser.add_argument('--roles', type=str, nargs='+', default=['user', 'verified'], help='Roles for the user')

    # API key command group
    apikey_parser = subparsers.add_parser('apikey', help='Manage API keys')
    apikey_subparsers = apikey_parser.add_subparsers(dest='apikey_command', required=True)
    create_apikey_parser = apikey_subparsers.add_parser('create', help='Create a new API key')
    create_apikey_parser.add_argument('username', type=str, help='Username to associate the key with')
    create_apikey_parser.add_argument('--description', type=str, default='', help='Description for the key')
    delete_apikey_parser = apikey_subparsers.add_parser('delete', help='Delete an API key')
    delete_apikey_parser.add_argument('key', type=str, help='API key to delete')
    list_apikey_parser = apikey_subparsers.add_parser('list', help='List API keys')
    list_apikey_parser.add_argument('--username', type=str, default=None, help='Optional username to filter by')

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

class PyInstrumentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip profiling for static files
        if request.url.path.startswith('/static') or request.url.path.startswith('/imgs'):
            return await call_next(request)
        
        profiler = Profiler()
        profiler.start()
        
        response = await call_next(request)
        
        profiler.stop()
        
        # Save profile to file if enabled
        if os.environ.get('PYINSTRUMENT_SAVE', 'false').lower() == 'true':
            profile_dir = Path('data/profiles')
            profile_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            profile_path = profile_dir / f"profile_{timestamp}_{request.url.path.replace('/', '_')}.html"
            with open(profile_path, 'w') as f:
                f.write(profiler.output_html())
        
        # Optionally add profile output to response headers for debugging
        # response.headers["X-Profile"] = profiler.output_text(unicode=True, color=False)[:1000]
        
        return response

def main():
    global app
    
    # Run migrations first, before anything else
    run_migrations()

    args = parse_args()

    # Handle CLI-only commands (no server startup needed)
    if args.command == 'user':
        from .coreplugins.user_service.mod import create_user  # noqa: lazy import
        from .coreplugins.user_service.models import UserCreate  # noqa: lazy import
        if args.user_command == 'create':
            import secrets
            password = args.password or secrets.token_urlsafe(16)
            user_create = UserCreate(username=args.username, email=args.email, password=password)
            asyncio.run(create_user(user_create, roles=args.roles, skip_verification=True))
            print(f"Created user: {args.username}")
            print(f"Email: {args.email}")
            print(f"Password: {password}")
            print(f"Roles: {args.roles}")
        else:
            print(f"Unknown user command: {args.user_command}")
            sys.exit(1)
        sys.exit(0)

    if args.command == 'apikey':
        from .coreplugins.api_keys.api_key_manager import api_key_manager  # noqa: lazy import
        if args.apikey_command == 'create':
            key_data = api_key_manager.create_key(args.username, description=args.description)
            print(f"Created API key for user: {args.username}")
            print(f"Key: {key_data['key']}")
            print(f"Description: {args.description}")
        elif args.apikey_command == 'delete':
            if api_key_manager.delete_key(args.key):
                print(f"Deleted API key: {args.key}")
            else:
                print(f"API key not found: {args.key}")
                sys.exit(1)
        elif args.apikey_command == 'list':
            keys = api_key_manager.list_keys(username=args.username)
            if keys:
                print(f"API keys:")
                for k in keys:
                    print(f"  {k['key']} - user: {k['username']} ({k.get('description', '')})")
            else:
                print("No API keys found")
        else:
            print(f"Unknown apikey command: {args.apikey_command}")
            sys.exit(1)
        sys.exit(0)

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
    
    # Add profiling middleware
    if os.environ.get('PYINSTRUMENT_ENABLE', 'false').lower() == 'true':
        app.add_middleware(PyInstrumentMiddleware)

    try:
        print(colored(f"Starting server on port {port}", "green"))
        uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on", timeout_graceful_shutdown=2)
    except Exception as e:
        print(colored(f"Error starting server: {str(e)}", "red"))

if __name__ == "__main__":
    main()
