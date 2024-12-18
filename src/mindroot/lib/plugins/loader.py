import os
import sys
import importlib
import termcolor
import traceback
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from .paths import get_plugin_path, get_plugin_import_path
from .manifest import list_enabled, load_plugin_manifest
from .installation import check_plugin_dependencies

app_instance = None

def load_middleware(app, plugin_name, plugin_path):
    """Load plugin middleware if it exists.
    
    Args:
        app (FastAPI): The FastAPI application instance
        plugin_name (str): Name of the plugin
        plugin_path (str): Import path of the plugin
    """
    try:
        middleware_module = importlib.import_module(f"{plugin_path}.middleware")
        if hasattr(middleware_module, 'middleware'):
            app.add_middleware(BaseHTTPMiddleware, dispatch=middleware_module.middleware)
            print(f"Added middleware for plugin: {plugin_name}")
    except ImportError:
        print(f"No middleware loaded for plugin: {plugin_name}")

def mount_static_files(app, plugin_name, category):
    """Mount plugin static files if they exist.
    
    Args:
        app (FastAPI): The FastAPI application instance
        plugin_name (str): Name of the plugin
        category (str): Plugin category ('core' or 'installed')
    """
    plugin_dir = get_plugin_path(plugin_name)
    if not plugin_dir:
        return
        
    dir_name = os.path.basename(plugin_dir)
    
    if category != 'core': 
        static_path = os.path.join(plugin_dir, 'src', dir_name, 'static')
        if not os.path.exists(static_path):
            static_path = os.path.join(plugin_dir, 'static')
    else:
        static_path = os.path.join(plugin_dir, 'static')

    if os.path.exists(static_path):
        app.mount(
            f"/{dir_name}/static", 
            StaticFiles(directory=static_path), 
            name=f"/{dir_name}/static"
        )
        print(termcolor.colored(
            f"Mounted static files for plugin: {plugin_name} at {static_path}", 
            'green'
        ))
    else:
        print(termcolor.colored(
            f"No static files found for plugin: {plugin_name}. Searched in {static_path}",
            'yellow'
        ))

async def load(app=None):
    """Load all enabled plugins.
    
    Args:
        app (FastAPI, optional): The FastAPI application instance
        
    Raises:
        Exception: If no FastAPI instance is provided or found
    """
    global app_instance

    # Setup app instance
    if app is not None:
        app_instance = app
    elif app_instance is not None:
        app = app_instance
    else:
        raise Exception("No FastAPI app instance provided or found")

    # Add project root to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Load enabled plugins
    enabled_plugins = list_enabled()
    failed_plugins = []

    for plugin_name, category in enabled_plugins:
        try:
            # Get plugin import path
            plugin_path = get_plugin_import_path(plugin_name)
            if not plugin_path:
                failed_plugins.append(
                    (plugin_name, f"Failed to locate plugin: {plugin_name}")
                )
                continue

            # Check dependencies for non-core plugins
            if category != 'core' and not check_plugin_dependencies(plugin_path):
                failed_plugins.append(
                    (plugin_name, f"Dependencies not met for plugin {plugin_name}")
                )
                continue

            # Import plugin module
            try:
                module = importlib.import_module(plugin_path)
            except ImportError:
                module = importlib.import_module(f"{plugin_path}.mod")

            print(termcolor.colored(
                f"Loaded plugin: {plugin_name} ({category})", 
                'green'
            ))

            # Call plugin initialization
            if hasattr(module, 'on_load'):
                print(termcolor.colored(
                    f"Calling on_load() for plugin: {plugin_name}",
                    'yellow', 'on_green'
                ))
                await module.on_load(app)

            # Load middleware
            load_middleware(app, plugin_name, plugin_path)

            # Load router if exists
            try:
                # we need to see if ther router.py actually exists
                # because if not this isn't an error, it just means there is no router
                # but if there is and we get an importerror, then we need to report that
                # as an error
                # so to detect if the file exists we need to import os
                plugin_dir = get_plugin_path(plugin_name)
                if not plugin_dir:
                    return
                    
                dir_name = os.path.basename(plugin_dir)
                
                if category != 'core': 
                    router_path = os.path.join(plugin_dir, 'src', dir_name, 'router.py')
                else:
                    router_path = os.path.join(plugin_dir, 'router.py')

                if os.path.exists(router_path):
                    router_module = importlib.import_module(f"{plugin_path}.router")
                    app.include_router(router_module.router)
                    print(termcolor.colored(
                        f"Included router for plugin: {plugin_name}",
                        'yellow'
                    ))
                else:
                    print(f"No router found for plugin: {plugin_name} at path {plugin_path}/router.py")

            except ImportError as e:
                trace = traceback.format_exc()
                print(termcolor.colored(
                    f"Failed to load router for plugin: {plugin_name}\n{str(e)}\n{trace}",'red'))
            # Mount static files
            mount_static_files(app, plugin_name, category)

        except Exception as e:
            trace = traceback.format_exc()
            failed_plugins.append(
                (plugin_name, f"Failed to load plugin: {str(e)}\n{trace}")
            )

    # Report failed plugins
    if failed_plugins:
        print(termcolor.colored("Failed to load the following plugins:", 'red'))
        for plugin_name, reason in failed_plugins:
            print(f"{plugin_name}: {reason}")
