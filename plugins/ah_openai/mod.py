import openai
from ..services import service
import os

@service(is_local=False)
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=100, num_gpu_layers=12):
    try:
        #model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"
        model = "meta-llama/Llama-3-70b-chat-hf"
        openai.api_key = os.environ.get("OPENAI_API_KEY")
        original_stream = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        async def content_stream(original_stream):
            for message in original_stream['choices'][0]['message']['content']:
                yield message['content']

        return content_stream(original_stream)

    except Exception as e:
        print('together.ai error:', e)

