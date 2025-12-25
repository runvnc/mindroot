Protocol-Based Typed Service Access
===================================

MindRoot provides a Protocol-based system for typed service access, enabling IDE autocomplete
and type checking when calling services.

Overview
--------

MindRoot services are dynamically registered and called via ``service_manager``. While flexible,
this loses type information. The Protocols system restores type safety:

.. code-block:: python

    from lib.providers.protocols import llm, image, tts

    # Full IDE autocomplete!
    stream = await llm.stream_chat('gpt-4', messages=[...], context=ctx)
    result = await image.generate('a red dragon', width=1024, context=ctx)
    audio = await tts.synthesize('Hello world', context=ctx)

Quick Start
-----------

Using Pre-instantiated Proxies (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to use typed services:

.. code-block:: python

    from lib.providers.protocols import llm, image, tts, stt, web_search

    # These are lazy proxies - they initialize on first use
    stream = await llm.stream_chat('gpt-4', messages=[...], context=ctx)
    result = await image.generate('a red dragon', context=ctx)

Creating Your Own Typed Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, create a typed proxy explicitly:

.. code-block:: python

    from lib.providers.protocols import LLM
    from lib.providers.services import service_manager

    llm: LLM = service_manager.typed(LLM)
    stream = await llm.stream_chat('gpt-4', messages=[...], context=ctx)

Available Protocols
-------------------

Core MindRoot provides these common Protocol definitions:

LLM (Language Model)
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class LLM(Protocol):
        async def stream_chat(self, model: str, messages: list = None,
                              context = None, temperature: float = 0.0,
                              max_tokens: int = 5000) -> AsyncIterator[str]: ...
        
        async def chat(self, model: str, messages: list,
                       context = None) -> str: ...
        
        async def format_image_message(self, pil_image, context = None) -> dict: ...
        
        async def get_service_models(self, context = None) -> dict: ...

Implemented by: ``ah_openai``, ``ah_anthropic``, ``ah_ollama``, ``mr_deepseek``, etc.

Image
~~~~~

.. code-block:: python

    class Image(Protocol):
        async def generate(self, prompt: str, width: int = 1024,
                          height: int = 1024, context = None) -> dict: ...

Implemented by: ``ah_flux``, ``ah_sd``, ``mr_imagen``, etc.

TTS (Text-to-Speech)
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class TTS(Protocol):
        async def synthesize(self, text: str, voice: str = 'default',
                            context = None) -> bytes: ...
        
        async def list_voices(self, context = None) -> list: ...

Implemented by: ``ah_tts``, ``mr_eleven_stream``, ``mr_f5_tts``, etc.

STT (Speech-to-Text)
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class STT(Protocol):
        async def transcribe(self, audio: bytes, context = None) -> str: ...
        
        async def transcribe_stream(self, audio_stream: AsyncIterator[bytes],
                                   context = None) -> AsyncIterator[str]: ...

Implemented by: ``mr_deepgram``, whisper plugins, etc.

WebSearch
~~~~~~~~~

.. code-block:: python

    class WebSearch(Protocol):
        async def search(self, query: str, num_results: int = 10,
                        context = None) -> list: ...

Plugin-Defined Protocols
------------------------

Plugins can define their own Protocols without modifying core MindRoot:

Defining a Protocol
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # In mr_sip/protocols.py
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class SIP(Protocol):
        """SIP telephony service protocol."""
        
        async def dial_service(self, destination: str,
                              context = None) -> dict: ...
        
        async def end_call_service(self, context = None) -> dict: ...
        
        async def sip_audio_out_chunk(self, audio_chunk: bytes,
                                      context = None) -> None: ...

Creating a Pre-instantiated Proxy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # In mr_sip/__init__.py or mr_sip/protocols.py
    from lib.providers.protocols.registry import create_lazy_proxy
    from .protocols import SIP

    # Create a lazy proxy for convenient access
    sip: SIP = create_lazy_proxy(SIP)

Using Plugin Protocols
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Users can then import and use:
    from mr_sip.protocols import sip

    result = await sip.dial_service('555-1234', context=ctx)
    await sip.end_call_service(context=ctx)

Protocol Registry
-----------------

Plugins can optionally register their Protocols for discovery:

Registering a Protocol
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from lib.providers.protocols import register_protocol
    from .protocols import SIP

    register_protocol('sip', SIP)

Discovering Protocols
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from lib.providers.protocols import get_protocol, list_protocols

    # List all registered protocols
    protocols = list_protocols()  # {'llm': LLM, 'image': Image, ...}

    # Get a specific protocol
    SIP = get_protocol('sip')
    if SIP:
        sip = service_manager.typed(SIP)

Method-to-Service Mapping
~~~~~~~~~~~~~~~~~~~~~~~~~

When a Protocol method name differs from the service name, use explicit mapping:

.. code-block:: python

    from lib.providers.protocols import map_method_to_service, Image

    # Map Image.generate() to the 'image' service
    map_method_to_service(Image, 'generate', 'image')

Backwards Compatibility
-----------------------

The Protocol system is fully backwards compatible. All existing code continues to work:

.. code-block:: python

    # This still works exactly as before
    from lib.providers.services import service_manager

    stream = await service_manager.stream_chat('gpt-4', messages=[...], context=ctx)
    result = await service_manager.image('a red dragon', context=ctx)

API Reference
-------------

service_manager.typed(protocol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get a typed proxy for a service protocol.

:param protocol: A Protocol class defining the service interface
:returns: A proxy object typed as the Protocol

.. code-block:: python

    llm: LLM = service_manager.typed(LLM)

service_manager.get_protocol(name)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get a registered Protocol by name.

:param name: The protocol name (e.g., 'llm', 'sip')
:returns: The Protocol class, or None if not found

.. code-block:: python

    SIP = service_manager.get_protocol('sip')

service_manager.list_protocols()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List all registered Protocols.

:returns: Dict mapping protocol names to Protocol classes

.. code-block:: python

    protocols = service_manager.list_protocols()
    # {'llm': LLM, 'image': Image, 'tts': TTS, ...}

create_lazy_proxy(protocol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a lazy typed proxy for a Protocol. Useful for plugins.

:param protocol: The Protocol class
:returns: A LazyTypedProxy typed as the Protocol

.. code-block:: python

    from lib.providers.protocols.registry import create_lazy_proxy
    
    sip: SIP = create_lazy_proxy(SIP)

register_protocol(name, protocol_class)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register a Protocol class for discovery.

:param name: A unique name for the protocol
:param protocol_class: The Protocol class

.. code-block:: python

    register_protocol('sip', SIP)

map_method_to_service(protocol, method_name, service_name)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create an explicit mapping from a Protocol method to a service name.

:param protocol: The Protocol class
:param method_name: The method name in the Protocol
:param service_name: The actual service name to call

.. code-block:: python

    map_method_to_service(Image, 'generate', 'image')
