import inspect
from .providers import ProviderManager

command_manager = ProviderManager()

def command(*, is_local=False):
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        command_manager.register_function(name, func, signature, docstring, is_local)
        return func
    return decorator

