import asyncio
import os
import time
import json
import requests

import os, asyncio
from together import AsyncTogether

async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
messages = [
    "What are the top things to do in San Francisco?",
    "What country is Paris in?",
]

async def async_chat_completion(messages):
    model = "cognitivecomputations/dolphin-2.5-mixtral-8x7b"

    async_client = AsyncTogether(api_key=os.environ.get("TOGETHER_API_KEY"))
    tasks = [
        async_client.chat.completions.create(
            model=model,  #"meta-llama/Llama-3-70b-chat-hf",
            messages=[{"role": "user", "content": message}],
        )
        for message in messages
    ]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(async_chat_completion(messages))

