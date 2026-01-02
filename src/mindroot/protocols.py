"""Convenience re-exports for Protocol-based typed service access.

Usage:
    from mindroot.protocols import LLM, Image, TTS, llm, image, tts
    
    # Consumer side - use pre-instantiated proxies
    stream = await llm.stream_chat('gpt-4', messages=[...])
    
    # Implementer side - inherit from Protocol for IDE autocomplete
    @service_class(LLM)
    class MyLLM(LLM):
        async def stream_chat(self, model: str, ...) -> AsyncIterator[str]:
            ...
"""

from mindroot.lib.providers.protocols import (
    # Protocol classes (for type hints and inheritance)
    LLM,
    Image,
    TTS,
    STT,
    WebSearch,
    # Pre-instantiated proxies (for consumers)
    llm,
    image,
    tts,
    stt,
    web_search,
    # Infrastructure (for advanced usage)
    ServiceProxy,
    LazyTypedProxy,
    register_protocol,
    get_protocol,
    list_protocols,
    map_method_to_service,
    implements,
    create_lazy_proxy,
    P,
)

__all__ = [
    # Protocol classes
    'LLM',
    'Image',
    'TTS',
    'STT',
    'WebSearch',
    # Pre-instantiated proxies
    'llm',
    'image',
    'tts',
    'stt',
    'web_search',
    # Infrastructure
    'ServiceProxy',
    'LazyTypedProxy',
    'register_protocol',
    'get_protocol',
    'list_protocols',
    'map_method_to_service',
    'implements',
    'create_lazy_proxy',
    'P',
]
