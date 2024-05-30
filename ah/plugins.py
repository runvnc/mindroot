import importlib
import json

import ah.hooks
import ah.commands
import ah.services

def load_ah(plugin_file):
    with open(plugin_file, 'r') as file:
        ah = json.load(file)
        for plugin in ah:
            if plugin.get('enabled'):
                plugin_name = plugin['name']
                try:
                    importlib.import_module(f"ah.{plugin_name}.mod")
                    print(f"Loaded plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")


load_ah('ah.json')

