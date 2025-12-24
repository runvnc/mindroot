"""Common Protocol definitions for core MindRoot services.

These Protocols define interfaces for commonly used services.
Plugins can import and use these, or define their own Protocols.

Note: These are optional conveniences. Plugins are free to define
their own Protocol classes without any dependency on this module.

Usage:
    from lib.providers.protocols import LLM, Image, TTS
    from lib.providers.services import service_manager
    
    llm: LLM = service_manager.typed(LLM)
    stream = await llm.stream_chat('gpt-4', messages=[...])
"""

from typing import Protocol, AsyncIterator, runtime_checkable, Any, Optional
from .registry import register_protocol, map_method_to_service


@runtime_checkable
class LLM(Protocol):
    """Language Model service protocol.
    
    Provides text generation and chat completion capabilities.
    Implemented by: ah_openai, ah_anthropic, ah_ollama, mr_deepseek, etc.
    """
    
    async def stream_chat(
        self,
        model: str,
        messages: list = None,
        context: Any = None,
        num_ctx: int = 200000,
        temperature: float = 0.0,
        max_tokens: int = 5000,
        num_gpu_layers: int = 0
    ) -> AsyncIterator[str]:
        """Stream chat completions from a language model.
        
        Args:
            model: Model identifier (e.g., 'gpt-4', 'claude-3-opus')
            messages: List of message dicts with 'role' and 'content'
            context: MindRoot context object
            num_ctx: Context window size
            temperature: Sampling temperature (0.0 = deterministic)
            max_tokens: Maximum tokens to generate
            num_gpu_layers: GPU layers for local models
            
        Yields:
            Text chunks as they're generated
        """
        ...
    
    async def chat(
        self,
        model: str,
        messages: list,
        context: Any = None,
        temperature: float = 0.0,
        max_tokens: int = 5000
    ) -> str:
        """Get a complete chat response (non-streaming).
        
        Args:
            model: Model identifier
            messages: List of message dicts
            context: MindRoot context object
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Complete response text
        """
        ...
    
    async def format_image_message(
        self,
        pil_image: Any,
        context: Any = None
    ) -> dict:
        """Format an image for inclusion in chat messages.
        
        Args:
            pil_image: PIL Image object
            context: MindRoot context object
            
        Returns:
            Dict formatted for the model's image input format
        """
        ...
    
    async def get_service_models(
        self,
        context: Any = None
    ) -> dict:
        """Get available models for this provider.
        
        Returns:
            Dict mapping service names to lists of model IDs
        """
        ...


@runtime_checkable
class Image(Protocol):
    """Image generation service protocol.
    
    Provides AI image generation capabilities.
    Implemented by: ah_flux, ah_sd, mr_imagen, etc.
    """
    
    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        context: Any = None,
        **kwargs
    ) -> dict:
        """Generate an image from a text prompt.
        
        Args:
            prompt: Text description of the image to generate
            width: Image width in pixels
            height: Image height in pixels
            context: MindRoot context object
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Dict with image data (typically includes 'url' or 'base64')
        """
        ...


@runtime_checkable
class TTS(Protocol):
    """Text-to-Speech service protocol.
    
    Provides speech synthesis capabilities.
    Implemented by: ah_tts, mr_eleven_stream, mr_f5_tts, etc.
    """
    
    async def synthesize(
        self,
        text: str,
        voice: str = 'default',
        context: Any = None,
        **kwargs
    ) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice identifier
            context: MindRoot context object
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Audio data as bytes
        """
        ...
    
    async def list_voices(
        self,
        context: Any = None
    ) -> list:
        """List available voices.
        
        Returns:
            List of voice identifiers or voice info dicts
        """
        ...


@runtime_checkable
class STT(Protocol):
    """Speech-to-Text service protocol.
    
    Provides speech recognition capabilities.
    Implemented by: mr_deepgram, whisper plugins, etc.
    """
    
    async def transcribe(
        self,
        audio: bytes,
        context: Any = None,
        **kwargs
    ) -> str:
        """Transcribe audio to text.
        
        Args:
            audio: Audio data as bytes
            context: MindRoot context object
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Transcribed text
        """
        ...
    
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        context: Any = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Transcribe streaming audio.
        
        Args:
            audio_stream: Async iterator of audio chunks
            context: MindRoot context object
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Transcribed text segments
        """
        ...


@runtime_checkable  
class WebSearch(Protocol):
    """Web search service protocol.
    
    Provides web search capabilities.
    """
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        context: Any = None,
        **kwargs
    ) -> list:
        """Search the web.
        
        Args:
            query: Search query
            num_results: Number of results to return
            context: MindRoot context object
            
        Returns:
            List of search result dicts
        """
        ...


# Register common protocols for discovery
register_protocol('llm', LLM)
register_protocol('image', Image)
register_protocol('tts', TTS)
register_protocol('stt', STT)
register_protocol('web_search', WebSearch)

# Map protocol methods to service names where they differ
# Image.generate() -> 'image' service (not 'generate')
map_method_to_service(Image, 'generate', 'image')
