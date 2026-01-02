import os
import sys
import inspect
from typing import Type, TypeVar, get_type_hints
from . import ProviderManager

# Ensure singleton across different import paths (lib.providers vs mindroot.lib.providers)
_SINGLETON_KEY = 'mindroot.lib.providers.services._service_manager'

if _SINGLETON_KEY in dir(sys.modules.get('builtins', {})):
    # Retrieve existing singleton
    service_manager = getattr(sys.modules['builtins'], _SINGLETON_KEY)
else:
    # Create new singleton and store it
    service_manager = ProviderManager()
    setattr(sys.modules['builtins'], _SINGLETON_KEY, service_manager)

P = TypeVar('P')  # Protocol type variable

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


def service_class(protocol: Type[P], *, flags=[]):
    """Class decorator that registers all Protocol methods as services.
    
    This enables class-based service implementations with IDE autocomplete
    when inheriting from a Protocol.
    
    Args:
        protocol: The Protocol class being implemented. Only methods defined
                  in this Protocol will be registered as services.
        flags: Optional flags to pass to each service registration.
    
    Example:
        from mindroot.services import service_class
        from mindroot.protocols import LLM
        
        @service_class(LLM)
        class DeepSeekLLM(LLM):
            async def stream_chat(self, model: str, messages: list = None,
                                  context = None, ...) -> AsyncIterator[str]:
                # IDE autocomplete works here!
                ...
            
            async def format_image_message(self, pil_image, context = None) -> dict:
                ...
    
    The decorator will:
    1. Instantiate the class (must have no required __init__ args)
    2. Find all methods that are defined in the Protocol
    3. Register each matching method as a service
    """
    def decorator(cls: Type) -> Type:
        # Get the protocol's method names (excluding dunder methods)
        protocol_methods = set()
        for name in dir(protocol):
            if not name.startswith('_'):
                attr = getattr(protocol, name, None)
                if callable(attr) or isinstance(inspect.getattr_static(protocol, name), (staticmethod, classmethod, property)) is False:
                    # Check if it's actually a method in the protocol
                    try:
                        if callable(getattr(protocol, name)):
                            protocol_methods.add(name)
                    except:
                        pass
        
        # Instantiate the class
        instance = cls()
        
        # Get module info from the class
        module = inspect.getmodule(cls)
        if module is None:
            raise ValueError(f"Cannot determine module of class {cls.__name__}")
        module_name = os.path.basename(os.path.dirname(module.__file__))
        
        # Register each protocol method
        for method_name in protocol_methods:
            if hasattr(instance, method_name):
                method = getattr(instance, method_name)
                if callable(method):
                    docstring = method.__doc__
                    signature = inspect.signature(method)
                    service_manager.register_function(
                        method_name, 
                        module_name, 
                        method, 
                        signature, 
                        docstring, 
                        flags
                    )
        
        return cls
    
    return decorator
