"""Protocol-based typed service access for MindRoot.

This module provides infrastructure for typed service access using Python Protocols,
enabling IDE autocomplete and type checking for MindRoot services.

## Quick Start (Recommended)

Use the pre-instantiated typed proxies for the cleanest API:

```python
from lib.providers.protocols import llm, image, tts

# Full IDE autocomplete!
stream = await llm.stream_chat('gpt-4', messages=[...])
result = await image.generate('a red dragon', width=1024)
audio = await tts.synthesize('Hello world', voice='alloy')
```

## Alternative: Create Your Own Proxy

```python
from lib.providers.protocols import LLM
from lib.providers.services import service_manager

llm: LLM = service_manager.typed(LLM)
stream = await llm.stream_chat('gpt-4', messages=[...])
```

## Plugin-Defined Protocols

Plugins can define their own Protocols without modifying core MindRoot:

```python
# In mr_sip/protocols.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class SIP(Protocol):
    async def dial_service(self, destination: str, context=None) -> dict: ...
    async def end_call_service(self, context=None) -> dict: ...

# In mr_sip/__init__.py
from lib.providers.protocols.registry import create_lazy_proxy
from .protocols import SIP

sip: SIP = create_lazy_proxy(SIP)

# Usage:
from mr_sip import sip
await sip.dial_service('555-1234')
```

## Protocol Registry

Plugins can optionally register their Protocols for discovery:

```python
from lib.providers.protocols import register_protocol
from .protocols import SIP

register_protocol('sip', SIP)

# Then others can discover:
from lib.providers.protocols import get_protocol, list_protocols
SIP = get_protocol('sip')
```

## Common Protocols

Core MindRoot provides common Protocol definitions:
- LLM - Language model services (stream_chat, chat, etc.)
- Image - Image generation (generate)
- TTS - Text-to-speech (synthesize, list_voices)
- STT - Speech-to-text (transcribe, transcribe_stream)
- WebSearch - Web search (search)

These are conveniences - plugins can define their own or extend these.
"""

from typing import TYPE_CHECKING

# Core infrastructure
from .registry import (
    ServiceProxy,
    LazyTypedProxy,
    register_protocol,
    get_protocol,
    list_protocols,
    map_method_to_service,
    implements,
    create_lazy_proxy,
    P,  # TypeVar for generic typing
)

# Common protocol definitions (optional conveniences)
from .common import (
    LLM,
    Image,
    TTS,
    STT,
    WebSearch,
)

# Pre-instantiated lazy proxies for convenient access
# These initialize on first use, so no import-time issues
llm: LLM = LazyTypedProxy(LLM)  # type: ignore[assignment]
image: Image = LazyTypedProxy(Image)  # type: ignore[assignment]
tts: TTS = LazyTypedProxy(TTS)  # type: ignore[assignment]
stt: STT = LazyTypedProxy(STT)  # type: ignore[assignment]
web_search: WebSearch = LazyTypedProxy(WebSearch)  # type: ignore[assignment]

__all__ = [
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
    # Protocol classes (for type hints and custom proxies)
    'LLM',
    'Image',
    'TTS',
    'STT',
    'WebSearch',
    # Pre-instantiated proxies (recommended for use)
    'llm',
    'image',
    'tts',
    'stt',
    'web_search',
]
