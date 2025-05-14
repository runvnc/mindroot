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
import uvicorn
from termcolor import colored
import socket
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# Load environment variables from .env file at the start
# Set override=True to make .env variables override existing environment variables
load_dotenv(override=True)

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Run the server")
    parser.add_argument("-p", "--port", type=int, help="Port to run the server on")
    # need to include optional admin-user and admin-password
    parser.add_argument("-u", "--admin-user", type=str, help="Admin username")
    parser.add_argument("-pw", "--admin-password", type=str, help="Admin password")
    return parser.parse_args()

def get_project_root():
    return Path(os.getcwd())
    #return Path(__file__).parent

def create_directories():
    root = get_project_root()
    directories = [
        "imgs",
        "data/chat",
        "models",
        "models/face",
        "models/llm",
        "static/personas",
        "personas",
        "personas/local",
        "personas/shared",
        "data/sessions"
    ]
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
    await plugins.load(app=app)
    app.mount("/static", StaticFiles(directory=str(root / "static"), follow_symlink=True), name="static")
    app.mount("/imgs", StaticFiles(directory=str(root / "imgs"), follow_symlink=True), name="imgs")

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
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

def main():
    global app

    cmd_args = parse_args()
    # save ALL parsed args in app state
    port = 8010
    if cmd_args.port:
        port = cmd_args.port
    else:
        cmd_args.port = port 
  
    app = FastAPI()

    #app.add_middleware(
    #    CORSMiddleware,
    #    allow_origins=["*"]  # This one line is all you need to allow all origins
    #)

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
