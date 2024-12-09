import json
import os
from datetime import datetime

# Central definition of manifest file location
MANIFEST_FILE = 'plugin_manifest.json'

def load_plugin_manifest():
    """Load the plugin manifest file.
    
    Returns:
        dict: The manifest data structure
    """
    abs_path = os.path.abspath(MANIFEST_FILE)
    if not os.path.exists(MANIFEST_FILE):
        create_default_plugin_manifest()

    with open(MANIFEST_FILE, 'r') as f:
        return json.load(f)

def save_plugin_manifest(manifest):
    """Save the plugin manifest file.
    
    Args:
        manifest (dict): The manifest data structure to save
    """
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

def update_plugin_manifest(plugin_name, source, source_path, remote_source=None, version="0.0.1", metadata=None):
    """Update or add a plugin entry in the manifest.
    
    Args:
        plugin_name (str): Name of the plugin
        source (str): Source type ('core', 'local', 'github')
        source_path (str): Path to the plugin
        remote_source (str, optional): GitHub repository reference
        version (str, optional): Plugin version
        metadata (dict, optional): Plugin metadata including commands and services
    """
    manifest = load_plugin_manifest()
    category = 'installed' if source != 'core' else 'core'
    
    # Try to read plugin_info.json if metadata not provided
    if not metadata and source_path:
        plugin_info_path = os.path.join(source_path, 'plugin_info.json')
        if os.path.exists(plugin_info_path):
            try:
                with open(plugin_info_path, 'r') as f:
                    metadata = json.load(f)
            except json.JSONDecodeError:
                metadata = None
    
    manifest['plugins'][category][plugin_name] = {
        'enabled': True,
        'source': source,
        'source_path': source_path,
        'version': version,
        'commands': metadata.get('commands', []) if metadata else [],
        'services': metadata.get('services', []) if metadata else [],
        'dependencies': metadata.get('dependencies', []) if metadata else []
    }
    
    if remote_source:
        manifest['plugins'][category][plugin_name]['remote_source'] = remote_source
    
    save_plugin_manifest(manifest)

def create_default_plugin_manifest():
    """Create a new default manifest file."""
    # read from default_plugin_manifest.json in same dir as this file
    default_manifest_path = os.path.join(os.path.dirname(__file__), 'default_plugin_manifest.json')
    with open(default_manifest_path, 'r') as f:
        default_manifest = json.load(f)
    save_plugin_manifest(default_manifest)

def toggle_plugin_state(plugin_name, enabled):
    """Toggle a plugin's enabled state.
    
    Args:
        plugin_name (str): Name of the plugin
        enabled (bool): New enabled state
        
    Returns:
        bool: True if successful, False if plugin not found
    """
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            manifest['plugins'][category][plugin_name]['enabled'] = enabled
            save_plugin_manifest(manifest)
            return True
    return False

def list_enabled(include_category=True):
    """List all enabled plugins.
    
    Args:
        include_category (bool): Whether to include the category in results
        
    Returns:
        list: List of enabled plugins, optionally with categories
    """
    enabled_list = []
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        for plugin_name, plugin_info in manifest['plugins'][category].items():
            if plugin_info.get('enabled'):
                if include_category:
                    enabled_list.append((plugin_name, category))
                else:
                    enabled_list.append(plugin_name)
    return enabled_list
