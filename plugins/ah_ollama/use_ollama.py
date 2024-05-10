import asyncio
from ollama import AsyncClient, Options


async def stream_chat(model, messages=[], num_ctx=2048, temperature=0.0, max_tokens=100):
    client = AsyncClient()
    try:
        print("GENERATING TEXT WITH MODEL:", model)
        return await client.chat(model=model,
                                 messages=messages,
                                 options=Options(temperature=temperature, num_predict=max_tokens),
                                 stream=True
                        )
    except ollama.ResponseError as e:
        print('Ollama error:', e.error)

async def list():
    client = AsyncClient()
    return await client.list()

async def unload(model):
    client = AsyncClient()
    return await client.generate(model=model, keep_alive=0)
