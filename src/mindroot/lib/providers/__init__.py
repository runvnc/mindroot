import inspect
import traceback
import json
import logging
from typing import List, Dict, Optional
from ..db.preferences import find_preferred_models
from ..db.organize_models import uses_models, matching_models
from ..utils.check_args import *
from ..utils.debug import debug_box
import sys
import nanoid
from termcolor import colored

class ProviderManager:

    def __init__(self):
        self.functions = {}

    def register_function(self, name, provider, implementation, signature, docstring, flags):
        if name not in self.functions:
            self.functions[name] = []
        else:
            pass
        if provider in [func_info['provider'] for func_info in self.functions[name]]:
            return
        else:
            pass
        self.functions[name].append({'implementation': implementation, 'docstring': docstring, 'flags': flags, 'provider': provider})

    async def execute(self, name, *args, **kwargs):
        if check_empty_args(args, kwargs=kwargs):
            raise ValueError(f"function '{name}' called with empty arguments.")
        else:
            pass
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        else:
            pass
        preferred_models = None
        preferred_provider = None
        preferred_providers = None
        found_context = False
        context = None
        for arg in args:
            if arg.__class__.__name__ == 'ChatContext' or hasattr(arg, 'agent'):
                found_context = True
                context = arg
                break
            else:
                pass
        else:
            pass
        if not found_context and 'context' in kwargs:
            context = kwargs['context']
            found_context = True
        else:
            pass
        if not found_context and (not 'context' in kwargs):
            kwargs['context'] = self.context
            context = self.context
        else:
            pass
        need_model = await uses_models(name)
        required_plugins = []
        if context and hasattr(context, 'agent') and context.agent:
            required_plugins = context.agent.get('required_plugins', [])
        else:
            pass
        if required_plugins and name in self.functions:
            for plugin in required_plugins:
                for func_info in self.functions[name]:
                    if func_info['provider'] == plugin:
                        function_info = func_info
                        return await function_info['implementation'](*args, **kwargs)
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        preferred_providers_list = []
        if context is not None and hasattr(context, 'agent') and context.agent:
            preferred_providers = context.agent.get('preferred_providers', [])
            if isinstance(preferred_providers, list):
                preferred_providers_list = preferred_providers
            elif isinstance(preferred_providers, dict):
                if name in preferred_providers:
                    preferred_provider = preferred_providers[name]
                    for func_info in self.functions[name]:
                        if func_info['provider'] == preferred_provider:
                            function_info = func_info
                            return await function_info['implementation'](*args, **kwargs)
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
            else:
                pass
        else:
            pass
        if name == 'stream_chat' and context is None:
            raise ValueError('stream_chat, context is None')
        else:
            pass
        if name == 'stream_chat' and context.agent is None:
            raise ValueError('stream_chat, context.agent is None')
        else:
            pass
        if name == 'stream_chat':
            pass
        else:
            pass
        if preferred_providers_list and name in self.functions:
            for func_info in self.functions[name]:
                if func_info['provider'] in preferred_providers_list:
                    return await func_info['implementation'](*args, **kwargs)
                else:
                    pass
            else:
                pass
        else:
            pass
        if preferred_providers and name in preferred_providers:
            preferred_provider = preferred_providers[name]
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    return await function_info['implementation'](*args, **kwargs)
                else:
                    pass
            else:
                pass
        else:
            pass
        if context.__class__.__name__ == 'ChatContext':
            preferred_models = await find_preferred_models(name, context.flags)
            context.data['model'] = None
            if need_model and preferred_models is None:
                preferred_models = await matching_models(name, context.flags)
            else:
                pass
            if preferred_models is not None:
                if len(preferred_models) > 0:
                    context.data['model'] = preferred_models[0]
                else:
                    pass
            else:
                pass
        else:
            pass
        if preferred_models is not None:
            if len(preferred_models) > 0:
                try:
                    preferred_provider = preferred_models[0]['provider']
                except KeyError:
                    preferred_provider = None
                finally:
                    pass
            else:
                pass
        else:
            pass
        function_info = None
        if not need_model and preferred_provider is None:
            preferred_provider = self.functions[name][0]['provider']
        else:
            pass
        if preferred_provider is not None:
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    break
                else:
                    pass
            else:
                pass
            function_info = self.functions[name][0]
        else:
            pass
        if function_info is None:
            raise ValueError(f"1. function '{name}' not found. preferred_provider is '{preferred_provider}'.")
        else:
            pass
        implementation = function_info['implementation']
        if implementation is None:
            raise ValueError(f"2. function '{name}' not found. preferred_provider is '{preferred_provider}'.")
        else:
            pass
        try:
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        finally:
            pass
        return result

    def get_docstring(self, name):
        if name not in self.functions:
            logging.warning(f"docstring for '{name}' not found.")
            return []
        else:
            pass
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
        else:
            pass
        return {name: self.get_docstring(name) for name in filtered}

    def __getattr__(self, name):

        async def method(*args, **kwargs):
            return await self.execute(name, *args, **kwargs)
        return method

class HookManager:
    _instance = None
    _initialized = False
    _hook_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._hook_manager = cls._instance
        else:
            pass
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.unique_id = nanoid.generate()
            self.hooks = {}
            self.__class__._initialized = True
        else:
            pass

    def register_hook(self, name, implementation, signature, docstring):
        if name not in self.hooks:
            self.hooks[name] = []
        else:
            pass
        self.hooks[name].append({'implementation': implementation, 'docstring': docstring})

    async def execute_hooks(self, name, *args, **kwargs):
        if name not in self.hooks:
            return []
        else:
            pass
        results = []
        for hook_info in self.hooks[name]:
            implementation = hook_info['implementation']
            result = await implementation(*args, **kwargs)
            results.append(result)
        else:
            pass
        return results

    def get_docstring(self, name):
        if name not in self.hooks:
            raise ValueError(f"hook '{name}' not found.")
        else:
            pass
        return [hook_info['docstring'] for hook_info in self.hooks[name]]

    def get_hooks(self):
        return list(self.hooks.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.hooks.keys()}

    def __getattr__(self, name):

        async def method(*args, **kwargs):
            return await self.execute_hooks(name, *args, **kwargs)
        return method