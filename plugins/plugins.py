import importlib
import json

import plugins.hooks
import plugins.commands
import plugins.services

def load_plugins(plugin_file):
    with open(plugin_file, 'r') as file:
        plugins = json.load(file)
        for plugin in plugins:
            if plugin.get('enabled'):
                plugin_name = plugin['name']
                try:
                    importlib.import_module(f"plugins.{plugin_name}.mod")
                    print(f"Loaded plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")


load_plugins('plugins.json')

