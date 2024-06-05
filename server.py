from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from ah import plugins

def create_directories():
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
        Path(directory).mkdir(parents=True, exist_ok=True)

create_directories()

import mimetypes
mimetypes.add_type("application/javascript", ".js", True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static", follow_symlink=True), name="static" )

app.mount("/imgs", StaticFiles(directory="imgs"), name="imgs")

from command_router import router as command_router
app.include_router(command_router)

from plugin_router import router as plugin_router
app.include_router(plugin_router)

# Include the router from chat.py
from ah.ah_chat.chat import router as chat_router
app.include_router(chat_router)

from persona_router import router as persona_router
app.include_router(persona_router)

from agent_router import router as agent_router
app.include_router(agent_router)


# Other server setup code can go here


