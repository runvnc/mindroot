import os
import json
from .manifest import load_plugin_manifest

async def get_command_plugin_mapping(context=None):
    """
    Get a mapping of commands to the plugins that provide them.
    
    Returns:
        dict: Mapping of command names to lists of plugin names
    """
    mapping = {}
    manifest = load_plugin_manifest()
    
    for category in manifest['plugins']:
        for plugin_name, plugin_info in manifest['plugins'][category].items():
            for command in plugin_info.get('commands', []):
                if command not in mapping:
                    mapping[command] = []
                mapping[command].append({
                    'name': plugin_name,
                    'category': category,
                    'enabled': plugin_info.get('enabled', False)
                })
    
    return mapping
