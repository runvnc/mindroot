"""Convenience re-exports for service registration.

Usage:
    from mindroot.services import service, service_class, service_manager
    
    @service()
    async def my_function(...):
        ...
    
    @service_class(LLM)
    class MyLLM(LLM):
        ...
"""

from mindroot.lib.providers.services import (
    service,
    service_class,
    service_manager,
)

__all__ = [
    'service',
    'service_class', 
    'service_manager',
]
