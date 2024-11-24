import os
import sys
from importlib.util import find_spec
from .manifest import load_plugin_manifest

def _get_project_root():
    """Get the absolute path to the project root directory.
    
    Returns:
        str: Absolute path to project root
    """
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return current_dir

def get_plugin_path(plugin_name):
    """Get the filesystem path for a plugin.
    
    Args:
        plugin_name (str): Name of the plugin
        
    Returns:
        str: Absolute path to the plugin directory or None if not found
    """
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            
            if plugin_info['source'] == 'core':
                # Use project root to build absolute path
                return os.path.join(_get_project_root(), 'coreplugins', plugin_name)
            elif plugin_info['source'] in ['local', 'github']:
                # source_path should already be absolute
                return plugin_info['source_path']
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    return None

def get_plugin_import_path(plugin_name):
    """Get the Python import path for a plugin.
    
    Args:
        plugin_name (str): Name of the plugin
        
    Returns:
        str: Import path for the plugin or None if not found
    """
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            
            if plugin_info['source'] == 'core':
                return f"coreplugins.{plugin_name}"
            elif plugin_info['source'] in ['local', 'github']:
                source_path = plugin_info['source_path']
                if not os.path.exists(source_path):
                    print(f"Warning: Plugin path does not exist: {source_path}")
                    return None
                    
                parent_dir = os.path.dirname(source_path)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                return os.path.basename(source_path)
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    return None
