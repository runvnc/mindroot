from pathlib import Path
from .mod import init_credit_system

# Initialize credit system with the current working directory
init_credit_system(str(Path.cwd()))

# Import services and commands
from .mod import *  # This imports all the services and commands
