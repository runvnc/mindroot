import os
import inspect
from . import ProviderManager

service_manager = ProviderManager()

def service(*, flags=[]):
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        module = inspect.getmodule(func)
        if module is None:
            raise ValueError("Cannot determine module of function")

        module_name = os.path.basename(os.path.dirname(module.__file__))
        service_manager.register_function(name, module_name, func, signature, docstring, flags)
        return func
    return decorator

