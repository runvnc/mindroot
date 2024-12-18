"""DEPRECATED: This module is maintained for backward compatibility.

Please use the new modular structure by importing from lib.plugins directly:
    from lib.plugins import (
        load, plugin_install, plugin_update, 
        get_plugin_path, get_plugin_import_path,
        load_plugin_manifest, save_plugin_manifest,
        toggle_plugin_state, list_enabled
    )
"""

import warnings

# Import everything from the new structure
from .plugins.loader import load, app_instance
from .plugins.installation import (
    plugin_install,
    plugin_update,
    check_plugin_dependencies,
    install_plugin_dependencies,
    download_github_files
)
from .plugins.manifest import (
    MANIFEST_FILE,
    load_plugin_manifest,
    save_plugin_manifest,
    update_plugin_manifest,
    create_default_plugin_manifest,
    toggle_plugin_state,
    list_enabled
)
from .plugins.paths import get_plugin_path, get_plugin_import_path

# Emit deprecation warning
warnings.warn(
    "Direct use of lib.plugins.py is deprecated. "
    "Please import from lib.plugins instead.",
    DeprecationWarning,
    stacklevel=2
)

# Export all symbols for backward compatibility
__all__ = [
    'load',
    'app_instance',
    'plugin_install',
    'plugin_update',
    'check_plugin_dependencies',
    'install_plugin_dependencies',
    'download_github_files',
    'MANIFEST_FILE',
    'load_plugin_manifest',
    'save_plugin_manifest',
    'update_plugin_manifest',
    'create_default_plugin_manifest',
    'toggle_plugin_state',
    'list_enabled',
    'get_plugin_path',
    'get_plugin_import_path'
]
