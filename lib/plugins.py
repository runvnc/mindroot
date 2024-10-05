import importlib
import json
import sys
import pkg_resources
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
import subprocess
from starlette.middleware.base import BaseHTTPMiddleware
from .route_decorators import public_route
import termcolor
from lib.providers.hooks import hook_manager
from importlib.util import find_spec
import traceback

from lib.providers import hooks
from lib.providers import commands
from lib.providers import services

app_instance = None
MANIFEST_FILE = 'plugin_manifest.json'

def get_plugin_path(plugin_name):
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            if plugin_info['source'] == 'local':
                return plugin_info['source_path']
            elif plugin_info['source'] == 'core':
                return f"coreplugins/{plugin_name}"
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    return None

def get_plugin_import_path(plugin_name):
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            if plugin_info['source'] == 'local':
                return plugin_info['source_path']
            elif plugin_info['source'] == 'core':
                return f"coreplugins.{plugin_name}"
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    return None

def list_enabled(include_category=True):
    enabled_list = []
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        for plugin_name, plugin_info in manifest['plugins'][category].items():
            if plugin_info.get('enabled'):
                print(f"{plugin_name} is enabled ({category})")
                if include_category:
                    enabled_list.append((plugin_name, category))
                else:
                    enabled_list.append(plugin_name)
            else:
                print(f"{plugin_name} is disabled ({category})")
    return enabled_list

def toggle_plugin_state(plugin_name, enabled):
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            manifest['plugins'][category][plugin_name]['enabled'] = enabled
            with open(MANIFEST_FILE, 'w') as f:
                json.dump(manifest, f, indent=2)
            return True
    return False

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

def plugin_install(plugin_name, source='pypi', source_path=None):
    if source == 'local':
        if not source_path:
            raise ValueError("source_path is required for local installation")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', source_path])
    elif source == 'pypi':
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', plugin_name])
    elif source == 'github':
        if not source_path:
            raise ValueError("source_path (GitHub URL) is required for GitHub installation")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'git+{source_path}'])
    else:
        raise ValueError(f"Unsupported installation source: {source}")
    
    update_plugin_manifest(plugin_name, source, source_path)
    return True

def plugin_update(plugin_name):
    plugin_path = get_plugin_path(plugin_name)
    if plugin_path:
        if install_plugin_dependencies(plugin_path):
            print(f"Plugin {plugin_name} updated successfully.")
            return True
    print(f"Failed to update plugin {plugin_name}.")
    return False

def load_plugin_manifest():
    if not os.path.exists(MANIFEST_FILE):
        create_default_plugin_manifest()

    with open(MANIFEST_FILE, 'r') as f:
        return json.load(f)

def update_plugin_manifest(plugin_name, source, source_path):
    manifest = load_plugin_manifest()
    category = 'installed' if source != 'core' else 'core'
    
    manifest['plugins'][category][plugin_name] = {
        'enabled': True,
        'source': source,
        'source_path': source_path if source == 'local' else None
    }
    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
def create_default_plugin_manifest():
    manifest = {
        'plugins': {
            'core': {
                'chat': {'enabled': True, 'source': 'core'},
                'agent': {'enabled': True, 'source': 'core'},
                'templates': {'enabled': True, 'source': 'core'}
            },
            'local': {},
            'installed': {}
        }
    }
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

def migrate_to_new_manifest():
    if os.path.exists('plugins.json') or os.path.exists('plugin_config.json'):
        manifest = {'plugins': {'core': {}, 'local': {}, 'installed': {}}}
        
        if os.path.exists('plugins.json'):
            with open('plugins.json', 'r') as f:
                old_plugins = json.load(f)
            for category in ['core', 'local', 'installed']:
                for plugin_name, plugin_info in old_plugins.get(category, {}).items():
                    manifest['plugins'][category][plugin_name] = {
                        'enabled': plugin_info.get('enabled', False),
                        'source': category
                    }
        
        if os.path.exists('plugin_config.json'):
            with open('plugin_config.json', 'r') as f:
                old_config = json.load(f)
            for plugin_name, plugin_info in old_config.get('installed_plugins', {}).items():
                category = 'core' if plugin_info['source'] == 'core' else 'installed'
                manifest['plugins'][category][plugin_name] = {
                    'enabled': True,
                    'source': plugin_info['source'],
                    'source_path': plugin_info.get('source_path')
                }
        
        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print("Migration to new manifest completed.")
        return True
    return False

async def load(app = None):
    global app_instance

    if app is not None:
        app_instance = app
    else:
        if app_instance is not None:
            app = app_instance
        else:
            raise Exception("No FastAPI app instance provided or found in plugin loader")

    if not os.path.exists(MANIFEST_FILE):
        if not migrate_to_new_manifest():
            create_default_plugin_manifest()

    manifest = load_plugin_manifest()
    enabled_plugins = list_enabled()
    print("Loading plugins...")
    print(manifest)
    print(enabled_plugins)
    for plugin_name, category in enabled_plugins:
        print(f"DEBUG: Processing plugin {plugin_name} in category {category}")
        plugin_info = manifest['plugins'][category].get(plugin_name)
        if not plugin_info:
            print(f"Plugin {plugin_name} is not in the manifest. Please reinstall it.")
            continue
        
        plugin_path = get_plugin_import_path(plugin_name)
        print(f"DEBUG: Plugin path for {plugin_name}: {plugin_path}")
        if not plugin_path:
            print(f"Failed to locate plugin: {plugin_name}")
            continue
        
        if category != 'core' and not check_plugin_dependencies(plugin_path):
            print(f"Dependencies not met for plugin {plugin_name}. Please update it.")
            continue
        try:
            try:
                print(f"DEBUG: Attempting to import module for {plugin_name}")
                module = importlib.import_module(plugin_path)
                print(f"DEBUG: Successfully imported module for {plugin_name}")
            except ImportError as e:
                print(f"DEBUG: ImportError for {plugin_name}: {str(e)}")
                print(f"DEBUG: Attempting to import {plugin_path}.mod for {plugin_name}")
                importlib.import_module(f"{plugin_path}.mod")
                print(f"DEBUG: Successfully imported {plugin_path}.mod for {plugin_name}")
            print(termcolor.colored(f"Loaded plugin: {plugin_name} ({category})", 'green'))
            
            load_middleware(app, plugin_name, plugin_path)
            
            if category == 'core':
                router_spec = find_spec(f"{plugin_path}.router")
                router_path = router_spec.origin if router_spec else None
            else:
                router_path = os.path.join(os.path.dirname(plugin_path), 'router.py')
            
            print(f"DEBUG: Checking for router at {router_path}")
            if router_path and (category == 'core' or os.path.exists(router_path)):
                print(f"DEBUG: Router file found for {plugin_name}")
                try:
                    print(f"DEBUG: Attempting to import router for {plugin_name}")
                    router_module = importlib.import_module(f"{plugin_path}.router")
                    print(f"DEBUG: Successfully imported router for {plugin_name}")
                    
                    for route in router_module.router.routes:
                        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
                            route.endpoint = public_route()(route.endpoint)
                    
                    app.include_router(router_module.router)
                    print(termcolor.colored(f"Included router for plugin: {plugin_name}", 'yellow'))
                except Exception as e:
                    trace = traceback.format_exc()
                    print(f"DEBUG: Error importing router for {plugin_name}: {str(e)} \n\n {trace}")
            else:
                print(f"DEBUG: No router file found for {plugin_name}")
            
            plugin_dir = get_plugin_path(plugin_name)
            static_path = os.path.join(plugin_dir, 'static')
            if os.path.exists(static_path):
                app.mount(f"/{plugin_name}/static", StaticFiles(directory=static_path), name=f"/{plugin_name}/static")
                print(termcolor.colored(f"Mounted static files for plugin: {plugin_name} at route path {static_path}", 'green'))

        except ImportError as e:
            # we need to make sure to include a traceback, so save that in a string first
            trace = traceback.format_exc()
            print(termcolor.colored(f"Failed to load plugin: {plugin_name}. Error: {e}", 'red'))

    await hook_manager.startup(app, context=None)
