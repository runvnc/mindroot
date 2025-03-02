import inspect
import traceback
import json
import logging
from typing import List, Dict, Optional
from ..db.preferences import find_preferred_models
from ..db.organize_models import uses_models, matching_models
from ..utils.check_args import *
import sys
import nanoid
from termcolor import colored


class ProviderManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, name, provider, implementation, signature, docstring, flags):
        if name not in self.functions:
            self.functions[name] = []

        if provider in [func_info['provider'] for func_info in self.functions[name]]:
            print(f"provider {provider} already registered for function {name}")
            return

        self.functions[name].append({
            'implementation': implementation,
            'docstring': docstring,
            'flags': flags,
            'provider': provider
        })
        print("registered function: ", name, provider, implementation, signature, docstring, flags)
    
    async def execute(self, name, *args, **kwargs):
        #print(f"execute: {name} called")

        if check_empty_args(args, kwargs=kwargs):
            raise ValueError(f"function '{name}' called with empty arguments.")

        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        preferred_models = None
        preferred_provider = None

        found_context = False
        context = None
        for arg in args:
            if arg.__class__.__name__ == 'ChatContext' or hasattr(arg, 'agent'):
                found_context = True
                context = arg
                break
        

        if not found_context and not ('context' in kwargs):
            kwargs['context'] = self.context
            context = self.context

        #print("context is ", context)
        need_model = await uses_models(name)

        # Check if any required plugins implement this command
        required_plugins = []
        if context and hasattr(context, 'agent') and context.agent:
            required_plugins = context.agent.get('required_plugins', [])
        
        # If we have required plugins, check if any implement this command
        if required_plugins and name in self.functions:
            for plugin in required_plugins:
                for func_info in self.functions[name]:
                    if func_info['provider'] == plugin:
                        function_info = func_info
                        return await function_info['implementation'](*args, **kwargs)
        
        if context.__class__.__name__ == 'ChatContext':
            preferred_models = await find_preferred_models(name, context.flags)
            context.data['model'] = None

            if need_model and preferred_models is None:
                #print("Did not find preferred, loading all matching based on flags")
                preferred_models = await matching_models(name, context.flags)
            
            if preferred_models is not None:
                if len(preferred_models) > 0:
                    context.data['model'] = preferred_models[0]

        if preferred_models is not None:
            if len(preferred_models) > 0:
                print("preferred models:", preferred_models)
                try:
                    preferred_provider = preferred_models[0]['provider']
                except KeyError:
                    print("provider key not found in preferred model")
                    print("preferred model:", preferred_models[0])
                    preferred_provider = None

        function_info = None

        if not need_model and (preferred_provider is None):
            preferred_provider = self.functions[name][0]['provider']


        if preferred_provider is not None:
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    break
            function_info = self.functions[name][0]

        if function_info is None:
            raise ValueError(f"1. function '{name}' not found. preferred_provider is '{preferred_provider}'.")

        implementation = function_info['implementation']

        if implementation is None:
            raise ValueError(f"2. function '{name}' not found. preferred_provider is '{preferred_provider}'.")

        try:
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    def get_docstring(self, name):
        if name not in self.functions:
            logging.warning(f"docstring for '{name}' not found.")
            return []
        return [func_info['docstring'] for func_info in self.functions[name]]

    def get_detailed_functions(self):
        return self.functions

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.functions.keys()}

    def get_some_docstrings(self, names):
        filtered = []
        for name in names:
            if name not in self.functions:
                logging.warning(f"agent function '{name}' not found")
            else:
                filtered.append(name)
        return {name: self.get_docstring(name) for name in filtered}

    def __getattr__(self, name):
        async def method(*args, **kwargs):
            return await self.execute(name, *args, **kwargs)

        return method


print(colored("Loading HookManager module", 'blue', 'on_yellow'))

class HookManager:
    _instance = None
    _initialized = False
    _hook_manager = None  # class-level storage for the instance
    
    def __new__(cls):
        print(colored(f"HookManager.__new__ called from:\n{traceback.format_stack()}", 'blue', 'on_white'))
        if cls._instance is None:
            print(colored("Creating new HookManager instance", 'white', 'on_blue'))
            cls._instance = super().__new__(cls)
            cls._hook_manager = cls._instance  # Store in class-level variable
        else:
            print(colored(f"Returning existing HookManager instance (id: {id(cls._instance)})", 'yellow', 'on_blue'))
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.unique_id = nanoid.generate()
            print(colored(f"HookManager initialized with id = {self.unique_id} from:\n{traceback.format_stack()}", 'white', 'on_blue'))
            self.hooks = {}
            self.__class__._initialized = True
        else:
            print(colored(f"Skipping HookManager re-initialization (id: {self.unique_id})", 'yellow', 'on_blue'))

    def register_hook(self, name, implementation, signature, docstring):
        print(colored(f"Registering hook {name} with HookManager (id: {self.unique_id})", 'white', 'on_blue', attrs=['bold']))
        if name not in self.hooks:
            self.hooks[name] = []
        self.hooks[name].append({
            'implementation': implementation,
            'docstring': docstring
        })

    async def execute_hooks(self, name, *args, **kwargs):
        if name not in self.hooks:
            print(colored(f"hook '{name}' not found.", 'yellow', 'on_blue'))
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
