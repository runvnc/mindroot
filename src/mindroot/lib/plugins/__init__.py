"""Plugin system for managing, installing, and loading plugins.

This module provides the main interface for the plugin system, including:
- Plugin installation and updates
- Plugin loading and initialization
- Manifest management
- Path resolution

Typical usage:
    from lib.plugins import load, plugin_install, toggle_plugin_state

    # Install a plugin
    plugin_install('my-plugin', source='github', source_path='user/repo')

    # Load plugins in FastAPI app
    await load(app)
"""

# Import main functionality from submodules
from .loader import pre_load, load
from .installation import (
    plugin_install,
    plugin_update,
    check_plugin_dependencies,
    install_plugin_dependencies
)
from .manifest import (
    load_plugin_manifest,
    save_plugin_manifest,
    update_plugin_manifest,
    toggle_plugin_state,
    list_enabled,
    MANIFEST_FILE
)
from .paths import get_plugin_path, get_plugin_import_path

# Export main functionality
__all__ = [
    'pre_load',
    'load',
    'plugin_install',
    'plugin_update',
    'check_plugin_dependencies',
    'install_plugin_dependencies',
    'load_plugin_manifest',
    'save_plugin_manifest',
    'update_plugin_manifest',
    'toggle_plugin_state',
    'list_enabled',
    'get_plugin_path',
    'get_plugin_import_path',
    'MANIFEST_FILE'
]
