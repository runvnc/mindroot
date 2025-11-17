from lib.providers.hooks import hook
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from datetime import datetime

@hook()
async def startup(app, context):
    static_dir = Path(__file__).parent / 'static'
    app.mount('/api_keys/static', StaticFiles(directory=str(static_dir)), name='api_keys_static')
    keys_dir = Path('data/apikeys')
    keys_dir.mkdir(parents=True, exist_ok=True)
from .api_key_manager import api_key_manager