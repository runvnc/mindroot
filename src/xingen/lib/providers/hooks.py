import inspect
from . import HookManager

hook_manager = HookManager()

def hook():
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        hook_manager.register_hook(name, func, signature, docstring)
        return func
    return decorator

print("hook should be defined?")
