import asyncio
from ollama import AsyncClient, Options


async def stream_chat(model, messages=[], temperature=0.0, max_tokens=260):
    client = AsyncClient()
    try:
        return await client.chat(model=model,
                                 format='json',
                                 messages=messages,
                                 options=Options(temperature=temperature),
                                 stream=True
                        )
    except ollama.ResponseError as e:
        print('Ollama error:', e.error)

async def list():
    client = AsyncClient()
    return await client.list()
