import asyncio
import json
import os
import logging
from datetime import datetime
from lib.providers.services import service, ServiceProvider

logger = logging.getLogger(__name__)

# Use paths relative to the process working directory
REQUEST_DIR = "data/password_resets/requests"
GENERATED_DIR = "data/password_resets/generated"
CHECK_INTERVAL_SECONDS = 30

@service()
async def process_password_reset_requests(context=None):
    """Processes password reset request files from a directory."""
    # Ensure directories exist
    os.makedirs(REQUEST_DIR, exist_ok=True)
    os.makedirs(GENERATED_DIR, exist_ok=True)

    sp = ServiceProvider()
    initiate_reset = sp.get('user_service.initiate_password_reset')
    
    if not (initiate_reset and callable(initiate_reset)):
        logger.error("Could not get 'user_service.initiate_password_reset' service.")
        return

    for filename in os.listdir(REQUEST_DIR):
        request_file_path = os.path.join(REQUEST_DIR, filename)
        if not os.path.isfile(request_file_path):
            continue

        try:
            with open(request_file_path, 'r') as f:
                data = json.load(f)
            
            username = data.get("username")
            is_admin_reset = data.get("is_admin_reset", False)

            if not username:
                raise ValueError("Username is missing from request file.")

            logger.info(f"Processing password reset request for user: {username}")
            token = await initiate_reset(username=username, is_admin_reset=is_admin_reset)
            
            reset_link = f"/user_service/reset-password/{token}"
            generated_file_path = os.path.join(GENERATED_DIR, f"{username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
            with open(generated_file_path, 'w') as f:
                json.dump({"username": username, "reset_link": reset_link, "token": token}, f, indent=2)
            
            logger.info(f"Successfully generated password reset link for {username}.")
            os.remove(request_file_path)

        except Exception as e:
            logger.error(f"Failed to process reset request file {filename}: {e}")
            error_file_path = os.path.join(REQUEST_DIR, f"{filename}.error")
            os.rename(request_file_path, error_file_path)

@service()
async def start_file_watcher_service(context=None):
    """Starts a background task to watch for password reset request files."""
    logger.info("Starting password reset file watcher service.")
    async def watcher_loop():
        while True:
            try:
                await process_password_reset_requests()
            except Exception as e:
                logger.error(f"Error in password reset watcher loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
    
    asyncio.create_task(watcher_loop())
