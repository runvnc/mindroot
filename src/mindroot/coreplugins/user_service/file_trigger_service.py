import asyncio
import json
import os
import logging
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from lib.providers.services import service, ServiceProvider

logger = logging.getLogger(__name__)

# Use paths relative to the process working directory
REQUEST_DIR = "data/password_resets/requests"
GENERATED_DIR = "data/password_resets/generated"
CHECK_INTERVAL_SECONDS = 5  # Reduced from 30 to 5 seconds as fallback

class PasswordResetHandler(FileSystemEventHandler):
    """Handler for file system events in the password reset request directory."""
    
    def __init__(self):
        super().__init__()
        self.sp = ServiceProvider()
        self.initiate_reset = self.sp.get('user_service.initiate_password_reset')
        
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
            
        file_path = event.src_path
        filename = os.path.basename(file_path)
        
        # Only process JSON files
        if not filename.endswith('.json'):
            return
            
        logger.info(f"New password reset request file detected: {filename}")
        
        # Process the file after a short delay to ensure it's fully written
        asyncio.create_task(self._process_file_delayed(file_path, filename))
    
    def on_moved(self, event):
        """Handle file move events (in case files are moved into the directory)."""
        if event.is_directory:
            return
            
        dest_path = event.dest_path
        filename = os.path.basename(dest_path)
        
        if not filename.endswith('.json'):
            return
            
        logger.info(f"Password reset request file moved into directory: {filename}")
        asyncio.create_task(self._process_file_delayed(dest_path, filename))
    
    async def _process_file_delayed(self, file_path, filename):
        """Process a file after a short delay to ensure it's fully written."""
        try:
            # Wait a moment to ensure file is fully written
            await asyncio.sleep(0.5)
            
            # Check if file still exists (might have been processed already)
            if not os.path.exists(file_path):
                logger.debug(f"File {filename} no longer exists, skipping")
                return
                
            await self._process_single_file(file_path, filename)
            
        except Exception as e:
            logger.error(f"Error in delayed processing of {filename}: {e}")
    
    async def _process_single_file(self, file_path, filename):
        """Process a single password reset request file."""
        if not (self.initiate_reset and callable(self.initiate_reset)):
            logger.error("Could not get 'user_service.initiate_password_reset' service.")
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            username = data.get("username")
            is_admin_reset = data.get("is_admin_reset", False)
            token = data.get("token")

            if not username:
                raise ValueError("Username is missing from request file.")

            logger.info(f"Processing password reset request for user: {username}")
            token = await self.initiate_reset(username=username, is_admin_reset=is_admin_reset, token=token)
            
            reset_link = f"/reset-password/{token}"
            generated_file_path = os.path.join(GENERATED_DIR, f"{username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
            
            # Ensure generated directory exists
            os.makedirs(GENERATED_DIR, exist_ok=True)
            
            with open(generated_file_path, 'w') as f:
                json.dump({
                    "username": username, 
                    "reset_link": reset_link, 
                    "token": token,
                    "generated_at": datetime.utcnow().isoformat()
                }, f, indent=2)
            
            logger.info(f"Successfully generated password reset link for {username} -> {generated_file_path}")
            
            # Remove the processed request file
            os.remove(file_path)
            logger.debug(f"Removed processed request file: {filename}")

        except Exception as e:
            logger.error(f"Failed to process reset request file {filename}: {e}")
            # Move to error file instead of renaming to avoid conflicts
            error_file_path = os.path.join(REQUEST_DIR, f"{filename}.error")
            try:
                os.rename(file_path, error_file_path)
                logger.info(f"Moved failed file to: {error_file_path}")
            except Exception as rename_error:
                logger.error(f"Failed to rename error file: {rename_error}")

@service()
async def process_password_reset_requests(context=None):
    """Processes password reset request files from a directory (fallback method)."""
    # Ensure directories exist
    os.makedirs(REQUEST_DIR, exist_ok=True)
    os.makedirs(GENERATED_DIR, exist_ok=True)

    sp = ServiceProvider()
    initiate_reset = sp.get('user_service.initiate_password_reset')
    
    if not (initiate_reset and callable(initiate_reset)):
        logger.error("Could not get 'user_service.initiate_password_reset' service.")
        return

    processed_count = 0
    for filename in os.listdir(REQUEST_DIR):
        request_file_path = os.path.join(REQUEST_DIR, filename)
        if not os.path.isfile(request_file_path) or not filename.endswith('.json'):
            continue

        # Skip error files
        if filename.endswith('.error'):
            continue

        try:
            with open(request_file_path, 'r') as f:
                data = json.load(f)
            
            username = data.get("username")
            is_admin_reset = data.get("is_admin_reset", False)
            token = data.get("token")

            if not username:
                raise ValueError("Username is missing from request file.")

            logger.info(f"Processing password reset request for user: {username} (fallback scan)")
            token = await initiate_reset(username=username, is_admin_reset=is_admin_reset, token=token)
            
            reset_link = f"/reset-password/{token}"
            generated_file_path = os.path.join(GENERATED_DIR, f"{username}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.json")
            with open(generated_file_path, 'w') as f:
                json.dump({
                    "username": username, 
                    "reset_link": reset_link, 
                    "token": token,
                    "generated_at": datetime.utcnow().isoformat()
                }, f, indent=2)
            
            logger.info(f"Successfully generated password reset link for {username} (fallback).")
            os.remove(request_file_path)
            processed_count += 1

        except Exception as e:
            logger.error(f"Failed to process reset request file {filename}: {e}")
            error_file_path = os.path.join(REQUEST_DIR, f"{filename}.error")
            try:
                os.rename(request_file_path, error_file_path)
            except Exception as rename_error:
                logger.error(f"Failed to rename error file: {rename_error}")
    
    if processed_count > 0:
        logger.info(f"Fallback scan processed {processed_count} files")

# Global observer instance
_file_observer = None

@service()
async def start_file_watcher_service(context=None):
    """Starts a file system watcher and background task to watch for password reset request files."""
    global _file_observer
    
    logger.info("Starting password reset file watcher service with real-time monitoring.")
    
    # Ensure directories exist
    os.makedirs(REQUEST_DIR, exist_ok=True)
    os.makedirs(GENERATED_DIR, exist_ok=True)
    
    try:
        # Set up file system watcher
        event_handler = PasswordResetHandler()
        _file_observer = Observer()
        _file_observer.schedule(event_handler, REQUEST_DIR, recursive=False)
        _file_observer.start()
        logger.info(f"File system watcher started for directory: {REQUEST_DIR}")
        
    except Exception as e:
        logger.error(f"Failed to start file system watcher: {e}")
        logger.info("Falling back to polling mode only")
    
    # Also run a background polling task as fallback
    async def watcher_loop():
        while True:
            try:
                await process_password_reset_requests()
            except Exception as e:
                logger.error(f"Error in password reset watcher loop: {e}")
            await asyncio.sleep(CHECK_INTERVAL_SECONDS)
    
    asyncio.create_task(watcher_loop())
    logger.info("Background polling task started as fallback")

@service()
async def stop_file_watcher_service(context=None):
    """Stops the file watcher service."""
    global _file_observer
    
    if _file_observer and _file_observer.is_alive():
        _file_observer.stop()
        _file_observer.join()
        logger.info("File system watcher stopped")
    else:
        logger.info("File system watcher was not running")
