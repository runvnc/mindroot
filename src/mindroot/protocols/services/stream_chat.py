from typing import AsyncIterator

class StreamChat(Protocol):
    async def stream_chat(self, prompt: str) -> AsyncIterator[str]:
        ...

