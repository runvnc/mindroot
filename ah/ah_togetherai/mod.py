import asyncio
from ..services import service
from together import AsyncTogether
import os

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        #model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"
        #model = "meta-llama/Llama-3-70b-chat-hf"
        model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
        async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
        original_stream = await async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
        )
        async def content_stream(original_stream):
            async for chunk in original_stream:
                yield chunk.choices[0].delta.content or ""

        return content_stream(original_stream)

    except Exception as e:
        print('together.ai error:', e)

