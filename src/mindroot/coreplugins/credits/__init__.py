from pathlib import Path
from .mod import init_credit_system
import asyncio

asyncio.run(init_credit_system(str(Path.cwd())))

from .mod import *  # This imports all the services and commands
