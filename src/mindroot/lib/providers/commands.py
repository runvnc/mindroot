import inspect
import os
from . import ProviderManager
from mindroot.lib.utils.debug import debug_box

command_manager = ProviderManager()

def command(*, flags=[]):
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        module = inspect.getmodule(func)
        if module is None:
            raise ValueError("Cannot determine module of function")

        module_name = os.path.basename(os.path.dirname(module.__file__))
        if module_name == 'l8n':
            debug_box("registering l8n command!" + name)
        command_manager.register_function(name, module_name, func, signature, docstring, flags)
        return func
    return decorator

