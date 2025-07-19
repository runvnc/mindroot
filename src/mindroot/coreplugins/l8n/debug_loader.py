#!/usr/bin/env python3
"""
Debug script to simulate the plugin loader behavior.
"""

import sys
import os
import importlib
from pathlib import Path

# Add the mindroot path
sys.path.insert(0, '/files/mindroot/src/mindroot')

try:
    print("Simulating plugin loader behavior...")
    
    # Simulate what the loader does
    plugin_name = 'l8n'
    category = 'core'
    
    # Get plugin path (simulating get_plugin_path)
    plugin_dir = '/files/mindroot/src/mindroot/coreplugins/l8n'
    print(f"Plugin directory: {plugin_dir}")
    
    # Check for middleware.py
    middleware_path = os.path.join(plugin_dir, 'middleware.py')
    print(f"Middleware path: {middleware_path}")
    print(f"Middleware exists: {os.path.exists(middleware_path)}")
    
    if os.path.exists(middleware_path):
        # Simulate get_plugin_import_path
        plugin_import_path = f'coreplugins.{plugin_name}'
        print(f"Plugin import path: {plugin_import_path}")
        
        # Try to import the module (this is what the loader does)
        print("\nAttempting to import module...")
        try:
            module = importlib.import_module(plugin_import_path)
            print(f"✅ Module imported: {module}")
        except ImportError as e:
            print(f"First import failed: {e}")
            try:
                module = importlib.import_module(f"{plugin_import_path}.mod")
                print(f"✅ Module imported via .mod: {module}")
            except ImportError as e2:
                print(f"❌ Both imports failed: {e2}")
                raise
        
        # Check if module has middleware
        print(f"\nModule has middleware: {hasattr(module, 'middleware')}")
        
        if hasattr(module, 'middleware'):
            middleware_func = module.middleware
            print(f"Middleware type: {type(middleware_func)}")
            print(f"Middleware callable: {callable(middleware_func)}")
            
            # This is what causes the error - let's check what we're actually getting
            print(f"Middleware repr: {repr(middleware_func)}")
            
            # Check if it's actually a function
            import inspect
            print(f"Is function: {inspect.isfunction(middleware_func)}")
            print(f"Is coroutine function: {inspect.iscoroutinefunction(middleware_func)}")
            
            if inspect.isfunction(middleware_func):
                print(f"Function signature: {inspect.signature(middleware_func)}")
            
            # Try to simulate what FastAPI does
            print("\nSimulating FastAPI middleware registration...")
            try:
                # This is essentially what BaseHTTPMiddleware does
                if callable(middleware_func):
                    print("✅ Middleware function is callable")
                else:
                    print("❌ Middleware function is not callable")
            except Exception as e:
                print(f"❌ Error checking callable: {e}")
        else:
            print("❌ Module does not have middleware attribute")
            print(f"Module attributes: {dir(module)}")
    
except Exception as e:
    print(f"❌ Error during simulation: {e}")
    import traceback
    traceback.print_exc()
