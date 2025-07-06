# Import all commands and services from mod.py
from .mod import *

# Install the monkey patch for Jinja2 template loading
from .monkey_patch import install_monkey_patch

# Auto-install the monkey patch when the plugin loads
install_monkey_patch()
