"""Protocol Registry for typed service access.

This module provides the infrastructure for typed service access using Python Protocols.
It allows both core MindRoot and plugins to define Protocol interfaces for services,
enabling IDE autocomplete and type checking.

Usage:
    # Option 1: Use pre-instantiated proxies (recommended)
    from lib.providers.protocols import llm, image
    stream = await llm.stream_chat('gpt-4', messages=[...])
    
    # Option 2: Create your own typed proxy
    from lib.providers.protocols import LLM
    from lib.providers.services import service_manager
    llm: LLM = service_manager.typed(LLM)
    stream = await llm.stream_chat('gpt-4', messages=[...])
    
    # Plugins can define their own Protocols:
    # In mr_sip/protocols.py:
    #   class SIP(Protocol):
    #       async def dial_service(...): ...
    #
    # Then import and use:
    #   from mr_sip import sip
    #   await sip.dial_service('555-1234')
"""

from typing import TypeVar, Type, Dict, Any, Optional, Callable, Generic
import logging

logger = logging.getLogger(__name__)

# Type variable for Protocol types
P = TypeVar('P')

# Global registry for protocol-to-service mappings
# Maps (protocol_class, method_name) -> service_name
_protocol_mappings: Dict[tuple, str] = {}

# Global registry for discovered protocols
# Maps protocol_name -> protocol_class
_protocol_registry: Dict[str, type] = {}


class ServiceProxy:
    """Proxy class that delegates method calls to service_manager with proper typing.
    
    This class is returned by service_manager.typed(Protocol) and provides
    IDE autocomplete by being cast to the Protocol type.
    
    The proxy intercepts method calls and routes them to the appropriate
    service via service_manager.execute().
    """
    
    def __init__(self, manager: Any, protocol: type):
        """
        Args:
            manager: The ProviderManager instance (service_manager)
            protocol: The Protocol class being proxied
        """
        self._manager = manager
        self._protocol = protocol
        self._method_cache: Dict[str, Callable] = {}
    
    def _get_service_name(self, method_name: str) -> str:
        """Get the service name for a protocol method.
        
        Checks for explicit mappings first, then falls back to using
        the method name directly as the service name.
        
        Args:
            method_name: The protocol method name
            
        Returns:
            The service name to call
        """
        # Check for explicit mapping
        key = (self._protocol, method_name)
        if key in _protocol_mappings:
            return _protocol_mappings[key]
        
        # Default: method name equals service name
        return method_name
    
    def __getattr__(self, name: str) -> Callable:
        """Intercept attribute access to create async method wrappers.
        
        Args:
            name: The method name being accessed
            
        Returns:
            An async function that calls the corresponding service
        """
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        # Check cache first
        if name in self._method_cache:
            return self._method_cache[name]
        
        service_name = self._get_service_name(name)
        
        async def method(*args, **kwargs):
            """Async wrapper that delegates to service_manager.execute()."""
            return await self._manager.execute(service_name, *args, **kwargs)
        
        # Cache the method
        self._method_cache[name] = method
        return method


class LazyTypedProxy(Generic[P]):
    """A lazy proxy that initializes on first use.
    
    This allows pre-instantiated typed proxies to be created at module
    import time without requiring service_manager to be fully initialized.
    
    Usage:
        # In protocols/__init__.py
        llm: LLM = LazyTypedProxy(LLM)
        
        # In user code
        from lib.providers.protocols import llm
        await llm.stream_chat('gpt-4', messages=[...])  # Initializes on first call
    """
    
    def __init__(self, protocol: Type[P]):
        """
        Args:
            protocol: The Protocol class to create a proxy for
        """
        object.__setattr__(self, '_protocol', protocol)
        object.__setattr__(self, '_proxy', None)
        object.__setattr__(self, '_initialized', False)
    
    def _get_proxy(self) -> ServiceProxy:
        """Get or create the underlying ServiceProxy."""
        if not object.__getattribute__(self, '_initialized'):
            from lib.providers.services import service_manager
            protocol = object.__getattribute__(self, '_protocol')
            proxy = ServiceProxy(service_manager, protocol)
            object.__setattr__(self, '_proxy', proxy)
            object.__setattr__(self, '_initialized', True)
        return object.__getattribute__(self, '_proxy')
    
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying proxy."""
        if name.startswith('_'):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        return getattr(self._get_proxy(), name)
    
    def __repr__(self) -> str:
        protocol = object.__getattribute__(self, '_protocol')
        initialized = object.__getattribute__(self, '_initialized')
        status = "initialized" if initialized else "lazy"
        return f"<LazyTypedProxy({protocol.__name__}) [{status}]>"


def register_protocol(name: str, protocol_class: type) -> None:
    """Register a Protocol class for discovery.
    
    Plugins can call this to make their Protocols discoverable
    via service_manager.get_protocol() or list_protocols().
    
    Args:
        name: A unique name for the protocol (e.g., 'sip', 'llm')
        protocol_class: The Protocol class
        
    Example:
        from lib.providers.protocols import register_protocol
        from .protocols import SIP
        
        register_protocol('sip', SIP)
    """
    if name in _protocol_registry:
        logger.warning(f"Protocol '{name}' is being re-registered")
    _protocol_registry[name] = protocol_class
    logger.debug(f"Registered protocol: {name}")


def get_protocol(name: str) -> Optional[type]:
    """Get a registered Protocol class by name.
    
    Args:
        name: The protocol name
        
    Returns:
        The Protocol class, or None if not found
        
    Example:
        SIP = get_protocol('sip')
        if SIP:
            sip = service_manager.typed(SIP)
    """
    return _protocol_registry.get(name)


def list_protocols() -> Dict[str, type]:
    """List all registered Protocols.
    
    Returns:
        Dict mapping protocol names to Protocol classes
    """
    return dict(_protocol_registry)


def map_method_to_service(
    protocol: type, 
    method_name: str, 
    service_name: str
) -> None:
    """Create an explicit mapping from a Protocol method to a service name.
    
    Use this when the Protocol method name differs from the service name.
    
    Args:
        protocol: The Protocol class
        method_name: The method name in the Protocol
        service_name: The actual service name to call
        
    Example:
        # Map Image.generate() to the 'image' service
        map_method_to_service(Image, 'generate', 'image')
    """
    key = (protocol, method_name)
    _protocol_mappings[key] = service_name
    logger.debug(f"Mapped {protocol.__name__}.{method_name} -> {service_name}")


def implements(protocol_method: Callable) -> Callable:
    """Decorator to declare that a service implements a Protocol method.
    
    This is an optional enhancement for @service that validates the
    implementation signature matches the Protocol.
    
    Args:
        protocol_method: The Protocol method being implemented
        
    Returns:
        Decorator function
        
    Example:
        from lib.providers.protocols import implements
        from lib.providers.protocols.common import LLM
        
        @service()
        @implements(LLM.stream_chat)
        async def stream_chat(model, messages=[], context=None):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Could add signature validation here in the future
        # For now, just return the function unchanged
        return func
    return decorator


def create_lazy_proxy(protocol: Type[P]) -> P:
    """Create a lazy typed proxy for a Protocol.
    
    This is a convenience function for plugins to create their own
    pre-instantiated proxies.
    
    Args:
        protocol: The Protocol class
        
    Returns:
        A LazyTypedProxy typed as the Protocol
        
    Example:
        # In mr_sip/__init__.py
        from lib.providers.protocols.registry import create_lazy_proxy
        from .protocols import SIP
        
        sip: SIP = create_lazy_proxy(SIP)
    """
    from typing import cast
    return cast(P, LazyTypedProxy(protocol))
