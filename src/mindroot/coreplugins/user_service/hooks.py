import asyncio
import logging
from lib.providers.hooks import hook
from lib.providers.services import ServiceProvider

logger = logging.getLogger(__name__)

@hook('startup')
async def on_user_service_startup(app, context=None):
    """
    Startup hook for the user_service plugin.
    """
    logger.info("User service startup hook triggered.")
    try:
        sp = ServiceProvider()
        start_watcher = sp.get('user_service.start_file_watcher_service')
        if start_watcher and callable(start_watcher):
            logger.info("Starting the password reset file watcher service via startup hook.")
            asyncio.create_task(start_watcher())
        else:
            logger.error("Could not find 'user_service.start_file_watcher_service' during startup.")
    except Exception as e:
        logger.error(f"Error starting file watcher service from hook: {e}")
