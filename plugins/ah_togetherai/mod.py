import asyncio
from ..services import service
from together import AsyncTogether
import os

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"

        async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
        stream = await async_client.chat.completions.create(
                model=model,  #"meta-llama/Llama-3-70b-chat-hf",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
        )
        # we need to transform the stream into another stream
        # extracting the context from the stream
        # new code here
        for chunk in stream:
            chunk.choices[0].delta.content or ""
            #print(chunk.choices[0].delta.content or "", end="", flush=True)

    except Exception as e:
        print('together.ai error:', e)

