from lib.providers.hooks import hook
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

@hook()
async def startup(app, context):
    startup_dir = context.startup_dir
    published_dir = Path(startup_dir) / 'published_indices'
    os.makedirs(published_dir, exist_ok=True)
    app.mount('/published', StaticFiles(directory=str(published_dir)), name='published_indices')