import inspect
import traceback
import json
import logging
from typing import List, Dict, Optional
from .preferences import find_preferred_models

class ProviderManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, name, provider, implementation, signature, docstring, flags):
        if name not in self.functions:
            self.functions[name] = []
        self.functions[name].append({
            'implementation': implementation,
            'docstring': docstring,
            'flags': flags,
            'provider': provider
        })

    async def execute(self, name, *args, **kwargs):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")

        # Check for preferred models
        preferred_models = await find_preferred_models(name, kwargs.get('flags', []))
        preferred_provider = preferred_models[0]['provider'] if preferred_models else None

        function_info = None
        if preferred_provider:
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    break
        if not function_info:
            function_info = self.functions[name][0]  # Fallback to the first function with the given name

        implementation = function_info['implementation']

        found_context = False
        for arg in args:
            if arg.__class__.__name__ == 'ChatContext':
                found_context = True
                break

        if not found_context and not ('context' in kwargs):
            kwargs['context'] = self.context

        try:
            print(f"about to execute {name}, args= {args}, kwargs={kwargs}")
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    def get_docstring(self, name):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        return [func_info['docstring'] for func_info in self.functions[name]]

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.functions.keys()}

    def get_some_docstrings(self, names):
        return {name: self.get_docstring(name) for name in names}

    def __getattr__(self, name):
        async def method(*args, **kwargs):
            print(f"method: {name} called")
            return await self.execute(name, *args, **kwargs)

        return method


import inspect

class HookManager:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, implementation, signature, docstring):
        if name not in self.hooks:
            self.hooks[name] = []
        self.hooks[name].append({
            'implementation': implementation,
            'docstring': docstring
        })

    async def execute_hooks(self, name, *args, **kwargs):
        if name not in self.hooks:
            return []
        results = []
        for hook_info in self.hooks[name]:
            implementation = hook_info['implementation']
            result = await implementation(*args, **kwargs)
            results.append(result)
        return results

    def get_docstring(self, name):
        if name not in self.hooks:
            raise ValueError(f"hook '{name}' not found.")
        return [hook_info['docstring'] for hook_info in self.hooks[name]]

    def get_hooks(self):
        return list(self.hooks.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.hooks.keys()}

    def __getattr__(self, name):
        async def method(*args, **kwargs):
            return await self.execute_hooks(name, *args, **kwargs)

        return method


