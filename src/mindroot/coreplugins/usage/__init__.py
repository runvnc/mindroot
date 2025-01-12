from pathlib import Path
from .mod import init_usage_tracking

# Initialize usage tracking with the current working directory
init_usage_tracking(str(Path.cwd()))

# Import services and commands
from .mod import *  # This imports all the services and commands
