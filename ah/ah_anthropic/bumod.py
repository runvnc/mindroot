import asyncio
from ..services import service
import anthropic
import os

@service()
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        model = "claude-3-5-sonnet-20240620"
        client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        original_stream = client.messages.stream(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
        )
        async def content_stream(original_stream):
            async for chunk in original_stream.text_stream:
                yield chunk

        return content_stream(original_stream)

    except Exception as e:
        print('claude.ai error:', e)
