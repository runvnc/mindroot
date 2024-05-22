import asyncio
import os
import time
import json
import requests

import os, asyncio
from together import AsyncTogether


messages = [
    "What is the capital of France?",
]

async def async_chat_completion(messages):
    model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"

    async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
    stream = await async_client.chat.completions.create(
            model=model,  #"meta-llama/Llama-3-70b-chat-hf",
            messages=[{"role": "user", "content": messages[0]}],
            stream=True
    )
    async for chunk in stream:
        print(chunk.choices[0].delta.content or "", end="", flush=True)

if __name__ == "__main__":
    asyncio.run(async_chat_completion(messages))

