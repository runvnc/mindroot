import anthropic
import os
import asyncio
import json
import time
from dotenv import load_dotenv
import websockets

load_dotenv(override=True)

client = anthropic.AsyncAnthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)
 
def get_model_abbreviations():
    return {
        "haiku": "claude-3-haiku-20240307",
        "sonnet": "claude-3-sonnet-20240229",
        "opus": "claude-3-opus-20240229"  
    }

async def stream_chat(**kwargs):
    global client
    abbrevs = get_model_abbreviations()
    args = {
        "model": 'haiku',
        "max_tokens": 180,
        "system": "You are an advanced AI teaching agent for children.",
        "temperature": 0
    }
    args.update(kwargs)

    if args['model'] in abbrevs:
        args['model'] = abbrevs[args['model']]
    if 'prompt' in args:
        del args['prompt']

    print("<<<<<<<<<<<<<<< final streaming llm args:", json.dumps(args, indent=4))
    async with client.messages.stream(**args) as stream:
        async for text in stream.text_stream:
            yield text


async def simple_ws_stream(websocket, **kwargs ):
    global client
    if 'prompt' in kwargs:
        kwargs['messages'] = [{"role": "user", "content": kwargs['prompt']}]
        
    async for chunk in stream_chat(**kwargs): 
        print(chunk)
        await websocket.send_json({"text": chunk})
        await asyncio.sleep(0.001)
        print("Sent text?")
    await websocket.send_json({"text": "", "finished": True})
    await asyncio.sleep(0.001)

async def start_fast_ws(websocket):
        defaults = {}
        async def receive_text():
            while True:
                try:
                    print("trying to receive on text request websocket")
                    data = await websocket.receive_json()
                    defaults.update(data)
                     
                    if not ('prompt' in data or 'messages' in data):
                        print("No 'prompt' or 'messages'. Set defaults only. Not prompting.")

                        await websocket.send_json({"text": "", "finished": True})
                        continue

                    print('----------------------------------------------------')
                    print("received text request: ", data)
                    print("sending request:", defaults)
                    await simple_ws_stream(websocket, **defaults)

                except websockets.exceptions.ConnectionClosed:
                    print("Error: LLM input websocket closed")
                    break

        print("creating receive_text task")
        receive_text_task = asyncio.create_task(receive_text())

        await asyncio.wait([receive_text_task])

def test():
    msgs = [{"role": "user", "content": "Reply with the answer ONLY. What is 10 * 2?"}]
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    start_time = time.time()
    stream = stream_chat(msgs)
    for text in stream:
        print(text, end="", flush=True)
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    print(f"\nDuration: {duration_ms:.2f} ms")

    quiz = """
You are an advanced educational AI agent. You output JSON data ONLY, with no commentary."
You will generate data for a quiz on a given subject.

Given subject: "country capitals"

Use this JSON format (example only!, adapt for quiz subject):

{
"quiz_title": "Country Capitals",
"question_format": "What is the capital of {question}?",
"questions": [
    { "q": "India", "a": "New Delhi" },
    { "q": "Mexico", "a": "Mexico City" },
    { "q":  "United States", "a": "Washington, D.C." }
  ]
}
    """
    msgs = [{"role": "user", "content": "Subject: vocabulary (2nd grade)"}]
    start_time = time.time()
    stream = stream_chat(client, msgs, system=quiz)
    for text in stream:
        print(text, end="", flush=True)
    end_time = time.time()
    duration_ms = (end_time - start_time) * 1000
    print(f"\nDuration: {duration_ms:.2f} ms")


if __name__ == "__main__":
    test()

