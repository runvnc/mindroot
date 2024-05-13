import importlib

def load_plugins(plugin_file):
    with open(plugin_file, 'r') as file:
        for line in file:
            plugin_name = line.strip()
            if plugin_name:
                try:
                    # Dynamically import the module
                    module = importlib.import_module(plugin_name)
                    print(f"Loaded plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")

load_plugins('plugins.json')

