import importlib
import json
import sys
import pkg_resources
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import subprocess
from starlette.middleware.base import BaseHTTPMiddleware
from ah.route_decorators import public_route
import termcolor
from .hooks import hook_manager

import ah.hooks
import ah.commands
import ah.services

app_instance = None

def get_plugin_path(plugin_name):
    for base_path in ['core', 'local', 'installed']:
        path = f"{base_path}/plugins/{plugin_name}"
        if os.path.exists(path):
            return path
    return None

def list_enabled(plugin_file = 'plugins.json'):
    enabled_list = []
    with open(plugin_file, 'r') as file:
        plugin_data = json.load(file)
        for category in ['core', 'local', 'installed']:
            for plugin_name, plugin_info in plugin_data.get(category, {}).items():
                if plugin_info.get('enabled'):
                    print(f"{plugin_name} is enabled ({category})")
                    enabled_list.append((plugin_name, category))
                else:
                    print(f"{plugin_name} is disabled ({category})")
    return enabled_list

def load_middleware(app, plugin_name, plugin_path):
    try:
        middleware_module = importlib.import_module(f"{plugin_path}.middleware")
        if hasattr(middleware_module, 'middleware'):
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware_module.middleware)
            print(f"Added middleware for plugin: {plugin_name}")
    except ImportError as e:
        print(f"No middleware loaded for plugin: {plugin_name}")

def check_plugin_dependencies(plugin_path):
    requirements_file = os.path.join(plugin_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        with open(requirements_file, 'r') as f:
            requirements = f.read().splitlines()
        for requirement in requirements:
            try:
                pkg_resources.require(requirement)
            except pkg_resources.DistributionNotFound:
                return False
    return True

def install_plugin_dependencies(plugin_path):
    requirements_file = os.path.join(plugin_path, 'requirements.txt')
    if os.path.exists(requirements_file):
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
            print(f"Installed dependencies for plugin: {os.path.basename(plugin_path)}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install dependencies for plugin: {os.path.basename(plugin_path)}. Error: {e}")
            return False
    return True

def plugin_install(plugin_name):
    plugin_path = get_plugin_path(plugin_name)
    if plugin_path:
        if install_plugin_dependencies(plugin_path):
            # Mark plugin as installed in configuration
            config = load_plugin_config()
            config['installed_plugins'][plugin_name] = True
            save_plugin_config(config)
            print(f"Plugin {plugin_name} installed successfully.")
            return True
    print(f"Failed to install plugin {plugin_name}.")
    return False

def plugin_update(plugin_name):
    plugin_path = get_plugin_path(plugin_name)
    if plugin_path:
        if install_plugin_dependencies(plugin_path):
            print(f"Plugin {plugin_name} updated successfully.")
            return True
    print(f"Failed to update plugin {plugin_name}.")
    return False

def load_plugin_config():
    config_path = 'plugin_config.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {'installed_plugins': {}}

def save_plugin_config(config):
    config_path = 'plugin_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f)

async def load(plugin_file = 'plugins.json', app = None):
    global app_instance

    if app is not None:
        app_instance = app
    else:
        if app_instance is not None:
            app = app_instance
        else:
            raise Exception("No FastAPI app instance provided or found in plugin loader")

    config = load_plugin_config()
    enabled_plugins = list_enabled(plugin_file)
    for plugin_name, category in enabled_plugins:
        plugin_path = get_plugin_path(plugin_name)
        if plugin_path:
            if not config['installed_plugins'].get(plugin_name, False):
                print(f"Plugin {plugin_name} is not installed. Please install it first.")
                continue
            if not check_plugin_dependencies(plugin_path):
                print(f"Dependencies not met for plugin {plugin_name}. Please update it.")
                continue
            try:
                importlib.import_module(f"{plugin_path}.mod")
                print(termcolor.colored(f"Loaded plugin: {plugin_name} ({category})", 'green'))
                
                load_middleware(app, plugin_name, plugin_path)
                
                router_path = f"{plugin_path}/router.py"
                if os.path.exists(router_path):
                    router_module = importlib.import_module(f"{plugin_path}.router")
                    
                    for route in router_module.router.routes:
                        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
                            route.endpoint = public_route()(route.endpoint)
                    
                    app.include_router(router_module.router)
                    print(termcolor.colored(f"Included router for plugin: {plugin_name}", 'yellow'))
                
                static_path = f"{plugin_path}/static"
                if os.path.exists(static_path):
                    app.mount(f"/{plugin_name}/static", StaticFiles(directory=static_path), name=f"/{plugin_name}/static")
                    print(termcolor.colored(f"Mounted static files for plugin: {plugin_name}", 'green'))
            except ImportError as e:
                print(termcolor.colored(f"Failed to load plugin: {plugin_name}. Error: {e}", 'red'))

    await hook_manager.startup(app, context=None)
