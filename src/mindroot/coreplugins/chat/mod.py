print("ah_chat module")
from lib.providers.hooks import hook
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path

@hook()
async def startup(app, context):
    startup_dir = context.startup_dir
    imgs_dir = Path(startup_dir) / 'imgs'
    os.makedirs(imgs_dir, exist_ok=True)
    
    app.mount("/imgs", StaticFiles(directory=str(imgs_dir)), name="imgs")
    print("Mounted imgs, dir: ", imgs_dir)
