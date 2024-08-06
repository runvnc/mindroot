import asyncio
from ..services import service
from together import AsyncTogether
import os
import termcolor

@service()
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        #model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"
        # model = "meta-llama/Llama-3-70b-chat-hf"
        #model = model
        model = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
        #model = "mistralai/Mixtral-8x22B-Instruct-v0.1"
        #model = "Qwen/Qwen1.5-110B-Chat"
        #model = "Qwen/Qwen2-72B-Instruct"
        async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
        original_stream = await async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=500 ,#max_tokens,
                stream=True
        )
        async def content_stream(original_stream):
            async for chunk in original_stream:
                # if AH_DEBUG set to True, print in green
                if os.environ.get("AH_DEBUG") == "True":
                    print(termcolor.colored(f'together.ai chunk: {chunk.choices[0].delta.content}', 'green'))
                yield chunk.choices[0].delta.content or ""

        return content_stream(original_stream)

    except Exception as e:
        print(termcolor.colored(f'together.ai error: {e}', 'red'))
        print('together.ai error:', e)

