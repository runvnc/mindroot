from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path
from .lib import plugins
import asyncio
import uvicorn
from termcolor import colored
import socket
# actually need a good way to part commmand line args

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Run the server")
    parser.add_argument("-p", "--port", type=int, help="Port to run the server on")
    return parser.parse_args()

def get_project_root():
    return Path(__file__).parent

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
    ]
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

create_directories()

import mimetypes
mimetypes.add_type("application/javascript", ".js", True)

app = None
templates = None

async def setup_app():
    global app, templates
    app = FastAPI()
    
    root = get_project_root()
    app.mount("/static", StaticFiles(directory=str(root / "static"), follow_symlink=True), name="static")
    app.mount("/imgs", StaticFiles(directory=str(root / "imgs")), name="imgs")

    await plugins.load(app=app)

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

def main():
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(setup_app())
    
    try:
        port = 8010
        cmd_args = parse_args()
        if cmd_args.port:
            port = cmd_args.port

        print(colored(f"Starting server on port {port}", "green"))
        uvicorn.run(app, host="0.0.0.0", port=port, lifespan="on")
    except Exception as e:
        print(colored(f"Error starting server: {str(e)}", "red"))

if __name__ == "__main__":
    main()
