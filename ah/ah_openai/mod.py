from ..services import service
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
 
client = openai.AsyncOpenAI()

@service()
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=3024, num_gpu_layers=12):
    try:
        stream = await client.chat.completions.create(
            model="gpt-4o",
            stream=True,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        async def content_stream(original_stream):
            async for chunk in original_stream:
                yield chunk.choices[0].delta.content or ""

        return content_stream(stream)

    except Exception as e:
        print('openai error:', e)

