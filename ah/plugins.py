import importlib
import json
from fastapi import FastAPI
from ah.server import app
import os

import ah.hooks
import ah.commands
import ah.services

def load_plugins(plugin_file, app):
    with open(plugin_file, 'r') as file:
        ah = json.load(file)
        for plugin in ah:
            if plugin.get('enabled'):
                plugin_name = plugin['name']
                try:
                    importlib.import_module(f"ah.{plugin_name}.mod")
                    print(f"Loaded plugin: {plugin_name}")
                    router_path = f"ah/{plugin_name}/router.py"
                    if os.path.exists(router_path):
                        router_module = importlib.import_module(f"ah.{plugin_name}.router")
                        app.include_router(router_module.router)
                        print(f"Included router for plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")


load_plugins('plugins.json', app)
