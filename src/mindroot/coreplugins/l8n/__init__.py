# Import all commands and services from mod.py
from .mod import *

# Import the middleware function for the plugin loader
from .middleware import middleware

# Install the monkey patch for Jinja2 template loading
from .monkey_patch import install_monkey_patch

# Auto-install the monkey patch when the plugin loads
# Only install once to prevent double installation
if not hasattr(install_monkey_patch, '_installed'):
    install_monkey_patch()
    install_monkey_patch._installed = True