import asyncio
import json
import os
import logging
from datetime import datetime
from lib.providers.services import service, ServiceProvider

logger = logging.getLogger(__name__)

# This file is kept for backward compatibility
# Password reset trigger functionality is now handled directly in router.py
logger.info("File trigger service loaded - functionality moved to router.py")