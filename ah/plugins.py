import importlib
import json
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from starlette.middleware.base import BaseHTTPMiddleware
from ah.route_decorators import public_route

import ah.hooks
import ah.commands
import ah.services

app_instance = None

def list_enabled(plugin_file = 'plugins.json'):
    list = []
    with open(plugin_file, 'r') as file:
        ah = json.load(file)
        for plugin in ah:
            if plugin.get('enabled'):
                print(f"{plugin['name']} is enabled")
                list.append(plugin['name'])
            else:
                print(f"{plugin['name']} is disabled")

    return list

def load_middleware(app, plugin_name):
    try:
        middleware_module = importlib.import_module(f"ah.{plugin_name}.middleware")
        if hasattr(middleware_module, 'middleware'):
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware_module.middleware)
            print(f"Added middleware for plugin: {plugin_name}")
    except ImportError as e:
        print(f"No middleware found for plugin: {plugin_name}. Error: {e}")

def load(plugin_file = 'plugins.json', app = None):
    global app_instance

    if app is not None:
        app_instance = app
    else:
        if app_instance is not None:
            app = app_instance
        else:
            raise Exception("No FastAPI app instance provided or found in plugin loader")

    with open(plugin_file, 'r') as file:
        ah = json.load(file)
        for plugin in ah:
            if plugin.get('enabled'):
                plugin_name = plugin['name']
                try:
                    importlib.import_module(f"ah.{plugin_name}.mod")
                    print(f"Loaded plugin: {plugin_name}")
                    
                    load_middleware(app, plugin_name)
                    
                    router_path = f"ah/{plugin_name}/router.py"
                    if os.path.exists(router_path):
                        router_module = importlib.import_module(f"ah.{plugin_name}.router")
                        
                        for route in router_module.router.routes:
                            if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
                                route.endpoint = public_route()(route.endpoint)
                        
                        app.include_router(router_module.router)
                        print(f"Included router for plugin: {plugin_name}")
                    static_path = f"ah/{plugin_name}/static"
                    if os.path.exists(static_path):
                        app.mount(f"/{plugin_name}/static", StaticFiles(directory=static_path), name=f"/{plugin_name}/static")
                        print(f"Mounted static files for plugin: {plugin_name}")
                except ImportError as e:
                    print(f"Failed to load plugin: {plugin_name}. Error: {e}")

        ah.hooks.hook_manager.startup(app, context=None)

    print(f"Plugin: {plugin_name} is disabled")

