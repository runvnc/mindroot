import asyncio
from ..services import service
import anthropic
import os

client = anthropic.AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


@service()
async def stream_chat(model, messages=[], context=None, num_ctx=200000, temperature=0.0, max_tokens=2500, num_gpu_layers=0):
    try:
        # first make a deep copy of the messages so that original aren't modified
        messages = [dict(message) for message in messages]

        model = "claude-3-5-sonnet-20240620"
        system = messages[0]['content']
        system = [{
            "type": "text",
            "text": system,
            "cache_control": { "type": "ephemeral" }
        }]
        messages = messages[1:]

        # remove any existing cache_control
        for message in messages:
            # check if converted to dict
            # if converted, remove any cache_control
            if isinstance(message, dict):
                if 'content' in message:
                    if isinstance(message['content'], list):
                        for content in message['content']:
                            if 'cache_control' in content:
                                del content['cache_control']

        for i in range(-1, -4, -1):
            if len(messages) >= abs(i):
                if isinstance(messages[i]['content'], str):
                    messages[i]['content'] = [{
                        "type": "text",
                        "text": messages[i]['content'],
                        "cache_control": { "type": "ephemeral" }
                    }]

        original_stream = await client.beta.prompt_caching.messages.create(
                model=model,
                system=system,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31,max-tokens-3-5-sonnet-2024-07-15"}
        )
        async def content_stream():
            async for chunk in original_stream:
                if chunk.type == 'content_block_delta':
                    if os.environ.get('AH_DEBUG') == 'True':
                        print('\033[92m' + chunk.delta.text + '\033[0m', end='')
                    yield chunk.delta.text
                else:
                    if os.environ.get('AH_DEBUG') == 'True':
                        # print all chunk data in cyan
                        print('\033[96m' + str(chunk) + '\033[0m', end='')
                    yield ''

        return content_stream()

    except Exception as e:
        print('claude.ai error:', e)
