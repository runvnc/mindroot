"""
Debug script to simulate the plugin loader behavior.
"""
import sys
import os
import importlib
from pathlib import Path
sys.path.insert(0, '/files/mindroot/src/mindroot')
try:
    plugin_name = 'l8n'
    category = 'core'
    plugin_dir = '/files/mindroot/src/mindroot/coreplugins/l8n'
    middleware_path = os.path.join(plugin_dir, 'middleware.py')
    if os.path.exists(middleware_path):
        plugin_import_path = f'coreplugins.{plugin_name}'
        try:
            module = importlib.import_module(plugin_import_path)
        except ImportError as e:
            try:
                module = importlib.import_module(f'{plugin_import_path}.mod')
            except ImportError as e2:
                raise
        if hasattr(module, 'middleware'):
            middleware_func = module.middleware
            import inspect
except Exception as e:
    import traceback
    traceback.print_exc()