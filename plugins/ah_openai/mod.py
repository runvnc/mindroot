from ..services import service
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
 
client = openai.AsyncOpenAI()

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o",
            stream=True,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        async def content_stream(original_stream):
            for message in stream['choices'][0]:
                yield message.delta.content or ""

        return content_stream(original_stream)

    except Exception as e:
        print('openai error:', e)

