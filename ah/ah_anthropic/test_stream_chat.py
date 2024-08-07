import asyncio
from mod import stream_chat

async def main():
    # Sample messages for the chat
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a very long story about a brave knight."}
    ]

    # Create a task for the streaming chat
    chat_task = asyncio.create_task(process_stream(messages))

    # Wait for 2 seconds before cancelling the task
    await asyncio.sleep(2)
    chat_task.cancel()

    try:
        await chat_task
    except asyncio.CancelledError:
        print("\nChat task was cancelled.")

async def process_stream(messages):
    try:
        stream = await stream_chat(model="claude-3-5-sonnet-20240620", messages=messages)
        async for chunk in stream:
            print(chunk, end='', flush=True)
    except asyncio.CancelledError:
        print("\nStream processing was interrupted.")
        raise

if __name__ == "__main__":
    asyncio.run(main())
