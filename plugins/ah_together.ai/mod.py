import asyncio
from ..services import service

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:

        print("GENERATING TEXT WITH MODEL:", model)
        return await client.chat(model=model,
                                 messages=messages,
                                 options=Options(temperature=temperature, low_vram=True, num_gpu=num_gpu_layers, num_predict=max_tokens),
                                 stream=True
                        )
    except ollama.ResponseError as e:
        print('Ollama error:', e.error)

