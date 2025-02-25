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

def _find_core_plugin_path(plugin_name):
    """Find the correct path for a core plugin, checking both development and installed locations.
    
    Args:
        plugin_name (str): Name of the core plugin
        
    Returns:
        str: Absolute path to the plugin directory or None if not found
    """
    # Try development path first
    dev_path = os.path.join(_get_project_root(), 'coreplugins', plugin_name)
    if os.path.exists(dev_path):
        #print(f"Found core plugin {plugin_name} in development path: {dev_path}")
        return dev_path
        
    # Try to find installed package
    try:
        import mindroot
        pkg_path = os.path.dirname(mindroot.__file__)
        installed_path = os.path.join(pkg_path, 'coreplugins', plugin_name)
        if os.path.exists(installed_path):
            print(f"Found core plugin {plugin_name} in installed path: {installed_path}")
            return installed_path
    except ImportError:
        pass
        
    # Try site-packages directly
    for path in sys.path:
        if 'site-packages' in path or 'dist-packages' in path:
            potential_path = os.path.join(path, 'mindroot', 'coreplugins', plugin_name)
            if os.path.exists(potential_path):
                print(f"Found core plugin {plugin_name} in site-packages: {potential_path}")
                return potential_path
                
    print(f"Warning: Could not find core plugin {plugin_name} in any location")
    return None

def get_plugin_path(plugin_name):
    """Get the filesystem path for a plugin.
    
    Args:
        plugin_name (str): Name of the plugin
        
    Returns:
        str: Absolute path to the plugin directory or None if not found
    """
    #print(f"Get plugin path: {plugin_name}")
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            
            if plugin_info['source'] == 'core':
                return _find_core_plugin_path(plugin_name)
            elif plugin_info['source'] in ['local', 'github']:
                # source_path should already be absolute
                if os.path.exists(plugin_info['source_path']):
                    return plugin_info['source_path']
                print(f"Warning: Plugin path does not exist: {plugin_info['source_path']}")
            else:
                print(f"Calling find_spec to get plugin path for {plugin_name}")
                spec = find_spec(plugin_name)
                if spec:
                    return spec.origin
                print(f"Warning: Could not find spec for plugin: {plugin_name}")
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
