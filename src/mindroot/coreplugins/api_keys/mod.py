from lib.providers.hooks import hook
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from datetime import datetime

print("--- API Keys Plugin Startup ---")

@hook()
async def startup(app, context):
    # Mount static files for UI
    static_dir = Path(__file__).parent / 'static'
    app.mount("/api_keys/static", StaticFiles(directory=str(static_dir)), name="api_keys_static")
    
    # Ensure API keys directory exists
    keys_dir = Path('data/apikeys')
    keys_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"API Keys plugin initialized. Keys directory: {keys_dir}")
    print(f"Mounted static files from: {static_dir}")

# Re-export the api_key_manager instance
from .api_key_manager import api_key_manager
