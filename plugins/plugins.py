import importlib
import json

def load_plugins(plugin_file):
    with open(plugin_file, 'r') as file:
        plugins = json.load(file)
        for plugin in plugins:
            if plugin.get('enabled'):
                plugin_name = plugin['name']
                try:
                    importlib.import_module(plugin_name)
                    print(f"Loaded plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")

load_plugins('plugins.json')

