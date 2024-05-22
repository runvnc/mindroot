import asyncio
import os
from together import AsyncTogether
from ..services import service

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))

    try:
        stream = await async_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": message} for message in messages],
            stream=True
        )
        async for chunk in stream:
            print(chunk.choices[0].delta.content or "", end="", flush=True)
        return stream

        print("GENERATING TEXT WITH MODEL:", model)
    except Exception as e:
        print('Together AI error:', str(e))

