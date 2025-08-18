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

# Import the new v2 preferences system with try/except for backward compatibility
try:
    from .model_preferences_v2 import ModelPreferencesV2
except ImportError:
    ModelPreferencesV2 = None

class ProviderManager:

    def __init__(self):
        self.functions = {}

    def register_function(self, name, provider, implementation, signature, docstring, flags):
        if name not in self.functions:
            self.functions[name] = []
        if provider in [func_info['provider'] for func_info in self.functions[name]]:
            return
        if name == 'say':
            debug_box('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            print("REGISTER:", name, provider)
        self.functions[name].append({'implementation': implementation, 'docstring': docstring, 'flags': flags, 'provider': provider})

    async def exec_with_provider(self, name, provider, *args, **kwargs):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        func_info = None
        for f in self.functions[name]:
            if f['provider'] == provider:
                func_info = f
                break
        
        implementation = func_info['implementation']
        if implementation is None:
            raise ValueError(f"function '{name}' not found for provider '{provider}'.")
        try:
            result = await implementation(*args, **kwargs)
        except Exception as e:
            raise e
        return result

    async def execute(self, name, *args, **kwargs):
        if check_empty_args(args, kwargs=kwargs):
            raise ValueError(f"function '{name}' called with empty arguments.")
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")

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
        if not found_context and 'context' in kwargs:
            context = kwargs['context']
            found_context = True

        if not found_context and (not 'context' in kwargs):
            kwargs['context'] = self.context
            context = self.context

        need_model = await uses_models(name)

        # DEBUG: Check what we have for model selection
        print(f"\n=== MODEL SELECTION DEBUG for {name} ===")
        print(f"args[0]: {args[0] if len(args) > 0 else 'N/A'}")
        print(f"kwargs.get('model'): {kwargs.get('model', 'N/A')}")
        if context and hasattr(context, 'agent') and context.agent:
            print(f"Agent service_models: {context.agent.get('service_models', 'N/A')}")
        else:
            print("No agent context or service_models")
        print("=== END DEBUG ===")

        if (len(args) > 0 and args[0] is None) and not 'model' in kwargs or ('model' in kwargs and kwargs['model'] is None):
            print("No model specified, checking service_models")
            if context is not None and context.agent is not None and 'service_models' in context.agent:
                service_models = context.agent['service_models']
                if name in service_models:
                    print("found service_models in agent")
                    print("set model (args[0]) to", service_models[name]['model'])
                    for func_info in self.functions[name]:
                        if func_info['provider'] == service_models[name]['provider']:
                            args = (service_models[name]['model'], *args[1:])
                            return await func_info['implementation'](*args, **kwargs)
                    print(f"WARNING: provider {service_models['name']['model']} specified for service {name}, but provider not enabled not enabled.")
            else:
                print("did not find service_models in agent")
                print('context.agent:', context.agent)
                
                # NEW V2 PREFERENCES LOGIC - Only as fallback when no agent-specific model
                if ModelPreferencesV2 is not None:
                    try:
                        print("No agent-specific model found, trying V2 system preferences...")
                        prefs_manager = ModelPreferencesV2()
                        ordered_providers = prefs_manager.get_ordered_providers_for_service(name)
                        
                        if ordered_providers:
                            print(f"Found V2 preferences for {name}: {ordered_providers}")
                            
                            for provider_name, model_name in ordered_providers:
                                # Check if this provider is available for this function
                                if name in self.functions:
                                    for func_info in self.functions[name]:
                                        if func_info['provider'] == provider_name:
                                            try:
                                                print(f"Trying V2 provider {provider_name} with model {model_name}")
                                                # Set the model as first argument if needed
                                                if len(args) > 0 and (args[0] is None or not args[0]):
                                                    args = (model_name, *args[1:])
                                                elif 'model' not in kwargs:
                                                    kwargs['model'] = model_name
                                                
                                                return await func_info['implementation'](*args, **kwargs)
                                            except Exception as e:
                                                print(f"V2 provider {provider_name} failed: {e}, trying next...")
                                                continue
                    except Exception as e:
                        print(f"V2 preferences failed: {e}, continuing with existing logic")
        else:
            print("Found possible model in zeroth arg:")
            if len(args) > 0:
                print(args[0])
                from coreplugins.admin.service_models import cached_get_service_models

                all_service_models = await cached_get_service_models()
                this_service_models = all_service_models.get(name, {})
                model_name = args[0]
                try:
                    if '__' in model_name:
                        #provider = model_name.split('__')[0]
                        model_name = model_name.split('__')[1]
                        
                    for provider, model_list in this_service_models.items():
                        if model_name in model_list:
                            print("found provider", provider)
                            for func_info in self.functions[name]:
                                if func_info['provider'] == provider:
                                    return await func_info['implementation'](*args, **kwargs)
                except Exception as e:
                    pass

        required_plugins = []
        if context and hasattr(context, 'agent') and context.agent:
            required_plugins = context.agent.get('required_plugins', [])
        if required_plugins and name in self.functions:
            for plugin in required_plugins:
                for func_info in self.functions[name]:
                    if func_info['provider'] == plugin:
                        function_info = func_info
                        return await function_info['implementation'](*args, **kwargs)

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
        if name == 'stream_chat' and context is None:
            raise ValueError('stream_chat, context is None')
        if name == 'stream_chat' and context.agent is None:
            raise ValueError('stream_chat, context.agent is None')

        if name == 'stream_chat':
            debug_box('execute stream_chat <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')

        if context is not None and hasattr(context, 'data') and 'PREFERRED_PROVIDER' in context.data:
            preferred_providers_list = [ context.data['PREFERRED_PROVIDER'] ]

        if preferred_providers_list and name in self.functions:
            for func_info in self.functions[name]:
                if func_info['provider'] in preferred_providers_list:
                    return await func_info['implementation'](*args, **kwargs)

        if preferred_providers and name in preferred_providers:
            preferred_provider = preferred_providers[name]
            for func_info in self.functions[name]:
                if func_info['provider'] == preferred_provider:
                    function_info = func_info
                    return await function_info['implementation'](*args, **kwargs)

        if context.__class__.__name__ == 'ChatContext':
            preferred_models = await find_preferred_models(name, context.flags)
            context.data['model'] = None
            if need_model and preferred_models is None:
                preferred_models = await matching_models(name, context.flags)
            if preferred_models is not None:
                if len(preferred_models) > 0:
                    context.data['model'] = preferred_models[0]

        if preferred_models is not None:
            if len(preferred_models) > 0:
                try:
                    preferred_provider = preferred_models[0]['provider']
                except KeyError:
                    preferred_provider = None
        function_info = None
        if not need_model and preferred_provider is None:
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
        return self.functions[name][0]['docstring']

    def get_detailed_functions(self):
        return self.functions

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self):
        return {name: self.get_docstring(name) for name in self.functions.keys()}

    def get_some_docstrings(self, names):
        debug_box("------------------------->>>>>>>>>>>>>>>>>>>>>>")
        print("Get some doc strings")
        print("self.functions", self.functions.keys())
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

class HookManager:
    _instance = None
    _initialized = False
    _hook_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._hook_manager = cls._instance
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.unique_id = nanoid.generate()
            self.hooks = {}
            self.__class__._initialized = True

    def register_hook(self, name, implementation, signature, docstring):
        if name not in self.hooks:
            self.hooks[name] = []
        self.hooks[name].append({'implementation': implementation, 'docstring': docstring})

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
