from ..services import service
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")
 
client = openai.AsyncOpenAI()

@service()
async def stream_chat(model, messages=[], context=None, num_ctx=2048, temperature=0.0, max_tokens=3724, num_gpu_layers=12):
    print("stream_chat called")
    print("model", model)
    try:
        if model == 'o1-preview':
            content = await sync_chat_o1(messages)

            async def content_stream_():
                yield content

            return content_stream_()

        stream = await client.chat.completions.create(
            model="chatgpt-4o-latest",
            #model="o1-preview",
            stream=True,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        async def content_stream(original_stream):
            async for chunk in original_stream:
                if os.environ.get('AH_DEBUG') == 'True':
                    print('\033[92m' + str(chunk.choices[0].delta.content) + '\033[0m', end='')

                yield chunk.choices[0].delta.content or ""

        return content_stream(stream)

    except Exception as e:
        print('openai error:', e)


from openai import OpenAI
sync_client = OpenAI()

async def sync_chat_o1(messages):
    messages_copy = messages.copy()
    messages_copy[0]['role'] = 'user'
    print("calling o1-preview")
    print("messages_copy", messages_copy)
    response = sync_client.chat.completions.create(
        model="o1-preview",
        messages = messages_copy
    )
    print("response from o1-preview received:")
    response = response.choices[0].message.content
    print(response)
    return response

