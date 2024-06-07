import inspect
from .providers import ProviderManager

command_manager = ProviderManager()

def command(*, is_local=False):
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        module = inspect.getmodule(func)
        if module is None:
            raise ValueError("Cannot determine module of function")

        module_name = os.path.basename(os.path.dirname(module.__file__))
 
        command_manager.register_function(name, module_name, func, signature, docstring, is_local)
        return func
    return decorator

