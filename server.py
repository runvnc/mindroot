from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from plugins import plugins

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

# Include the router from chat.py
from plugins.ah_chat.chat import router as chat_router
app.include_router(chat_router)

# Other server setup code can go here
