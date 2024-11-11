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
from ah.lib.providers.hooks import hook_manager
from importlib.util import find_spec
import traceback
# need temppfile
import tempfile
# need shutil
import shutil
import requests
import zipfile
import os

from .providers import hooks, commands, services

app_instance = None
MANIFEST_FILE = 'plugin_manifest.json'

def download_github_files(repo_path, tag=None):
    """Download GitHub repo files to temp directory"""
    # Format the download URL
    if tag:
        download_url = f"https://github.com/{repo_path}/archive/refs/tags/{tag}.zip"
    else:
        download_url = f"https://github.com/{repo_path}/archive/refs/heads/main.zip"
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'repo.zip')
    
    try:
        # Download the zip file
        response = requests.get(download_url)
        response.raise_for_status()
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            
        # Find plugin_info.json
        for root, _, files in os.walk(temp_dir):
            if 'plugin_info.json' in files:
                with open(os.path.join(root, 'plugin_info.json'), 'r') as f:
                    plugin_info = json.load(f)
                return temp_dir, root, plugin_info
                
        raise ValueError("No plugin_info.json found in repository")
        
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise e

def get_plugin_path(plugin_name):
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            if plugin_info['source'] == 'available':
                return plugin_info['source_path']
            elif plugin_info['source'] == 'core':
                return f"src/xingen/coreplugins/{plugin_name}"
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    return None

def get_plugin_import_path(plugin_name):
    manifest = load_plugin_manifest()
    for category in manifest['plugins']:
        if plugin_name in manifest['plugins'][category]:
            plugin_info = manifest['plugins'][category][plugin_name]
            print(f"DEBUG: Plugin info for {plugin_name}: {plugin_info}")
            if plugin_info['source'] == 'available':
                source_path = plugin_info['source_path']
                print(f"DEBUG: Available plugin path for {plugin_name}: {source_path}")
                if not os.path.exists(source_path):
                    print(f"DEBUG: Plugin path does not exist: {source_path}")
                    return None
                parent_dir = os.path.dirname(source_path)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                return os.path.basename(source_path)
            elif plugin_info['source'] == 'core':
                return f"coreplugins.{plugin_name}"
            else:
                spec = find_spec(plugin_name)
                return spec.origin if spec else None
    print(f"DEBUG: Plugin {plugin_name} not found in manifest")
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

def github_to_pip(github_ref):
    # Split into parts (user/repo or user/repo:tag)
    parts = github_ref.split(':')
    repo_path = parts[0]
    tag = parts[1] if len(parts) > 1 else None
    
    # Build pip install URL
    base_url = f"git+https://github.com/{repo_path}.git"
    if tag:
        base_url += f"@{tag}"
    
    return base_url

def plugin_install(plugin_name, source='pypi', source_path=None):
    try:
        if source == 'available':
            if not source_path:
                raise ValueError("source_path is required for available installation")
            if not os.path.isfile(os.path.join(source_path, 'setup.py')) and not os.path.isfile(os.path.join(source_path, 'pyproject.toml')):
                raise ValueError(f"{source_path} does not appear to be a valid Python project: neither 'setup.py' nor 'pyproject.toml' found")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', source_path])
        elif source == 'pypi':
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', plugin_name])
        elif source == 'github':
            if not source_path:
                raise ValueError("source_path (e.g. repo/name or repo/name:tag) is required")
            
            # Split into parts (user/repo and optional tag)
            parts = source_path.split(':')
            repo_path = parts[0]
            tag = parts[1] if len(parts) > 1 else None
            
            try:
                # Download and get plugin info
                temp_dir, plugin_root, plugin_info = download_github_files(repo_path, tag)
                plugin_name = plugin_info['name']  # Get actual plugin name
                
                # Install directly from downloaded files
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', plugin_root])
                
                # Update manifest with github source
                update_plugin_manifest(
                    plugin_name,
                    source='github',
                    source_path=f"{repo_path}:{tag}" if tag else repo_path,
                    version=plugin_info.get('version', '0.0.1')
                )
                
                return True
                
            finally:
                # Clean up temp directory
                if 'temp_dir' in locals():
                    shutil.rmtree(temp_dir)
        else:
            raise ValueError(f"Unsupported installation source: {source}")
        
        update_plugin_manifest(plugin_name, source, source_path)
        return True

    except subprocess.CalledProcessError as e:
        error_message = e.output.decode() if e.output else str(e)
        raise RuntimeError(f"Pip installation failed: {error_message}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error during installation: {str(e)}")

def plugin_update(plugin_name):
    return plugin_install(plugin_name)

def load_plugin_manifest():
    if not os.path.exists(MANIFEST_FILE):
        create_default_plugin_manifest()

    with open(MANIFEST_FILE, 'r') as f:
        return json.load(f)

def save_plugin_manifest(manifest):    
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)

def update_plugin_manifest(plugin_name, source, source_path, version="0.0.1"):
    manifest = load_plugin_manifest()
    category = 'installed' if source != 'core' else 'core'
    
    manifest['plugins'][category][plugin_name] = {
        'enabled': True,
        'source': source,
        'source_path': source_path if source == 'available' else None,
        'version': version
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
            'available': {},
            'installed': {}
        }
    }
    with open(MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
        
def migrate_to_new_manifest():
    if os.path.exists('plugins.json') or os.path.exists('plugin_config.json'):
        manifest = {'plugins': {'core': {}, 'available': {}, 'installed': {}}}
        
        if os.path.exists('plugins.json'):
            with open('plugins.json', 'r') as f:
                old_plugins = json.load(f)
            for category in ['core', 'available', 'installed']:
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

    # Add the main project directory to sys.path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # This is the parent directory of lib/
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

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
                print("plugin_path = ", plugin_path)
            except ImportError as e:
                print(f"DEBUG: ImportError for {plugin_name}: {str(e)}")
                print(f"DEBUG: Attempting to import {plugin_path}.mod for {plugin_name}")
                module = importlib.import_module(f"{plugin_path}.mod")
                print(f"DEBUG: Successfully imported {plugin_path}.mod for {plugin_name}")
            print(termcolor.colored(f"Loaded plugin: {plugin_name} ({category})", 'green'))
            if hasattr(module, 'on_load'):
                print(termcolor.colored(f"Calling on_load() hook for plugin: {plugin_name}", 'yellow', 'on_green'))
                await module.on_load(app)

            load_middleware(app, plugin_name, plugin_path)
            
            if True or category == 'core':
                router_spec = find_spec(f"{plugin_path}.router")
                print("router_spec:", router_spec)
                router_path = router_spec.origin if router_spec else None
                print("Core plugin, router_path is", router_path)
            else:
                print("Non-core plugin, plugin_path is", plugin_path)
                router_path = os.path.join(os.path.dirname(plugin_path), 'router.py')
            print(f"DEBUG: Checking for router at {router_path}")
            if True or router_path and (category == 'core' or os.path.exists(router_path)):
                print(f"DEBUG: Router file found for {plugin_name}")
                try:
                    print(f"DEBUG: Attempting to import router for {plugin_name}")
                    print("Importing: ", f"{plugin_path}.router")
                    router_module = importlib.import_module(f"{plugin_path}.router")
                    print(f"DEBUG: Successfully imported router for {plugin_name}")
                    
                    for route in router_module.router.routes:
                        print("Found route:", route)
                        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__public_route__'):
                            print("Public route")
                            route.endpoint = public_route()(route.endpoint)
                        else:
                            print("Not a public route")

                    app.include_router(router_module.router)
                    print(termcolor.colored(f"Included router for plugin: {plugin_name}", 'yellow'))
                except ImportError as e:
                    trace = traceback.format_exc()
                    print(f"DEBUG: No router found (may not be an error) or import error for {plugin_name}: {str(e)} \n\n {trace}")
                except Exception as e:
                    trace = traceback.format_exc()
                    print(f"DEBUG: No router found or other error for {plugin_name}: {str(e)} \n\n {trace}")
            else:
                print(f"DEBUG: No router file found for {plugin_name}")
            
            plugin_dir = get_plugin_path(plugin_name)
            dir_name = plugin_dir.split('/')[-1]

            if category != 'core': 
                static_path = os.path.join(plugin_dir, 'src', dir_name, 'static')
            else:
                static_path = os.path.join(plugin_dir, 'static')

            if os.path.exists(static_path):
                app.mount(f"/{dir_name}/static", StaticFiles(directory=static_path), name=f"/{dir_name}/static")
                print(termcolor.colored(f"Mounted static files for plugin: {plugin_name} at route path {static_path}", 'green'))

        except ImportError as e:
            # we need to make sure to include a traceback, so save that in a string first
            trace = traceback.format_exc()
            print(termcolor.colored(f"Failed to load plugin: {plugin_name}. Error: {e}\n\{trace}", 'red'))

