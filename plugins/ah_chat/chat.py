from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from ..ah_agent import agent
import asyncio

router = APIRouter()


class Message(BaseModel):
    message: str

sse_clients = set()

@router.get("/chat/events")
async def chat_events(request: Request):
    async def event_generator():
        queue = asyncio.Queue()
        sse_clients.add(queue)
        try:
            while True:
                data = await queue.get()
                yield data
        except asyncio.CancelledError:
            sse_clients.remove(queue)

    return EventSourceResponse(event_generator())

async def send_event_to_clients(event: str, data: dict):
    print("Try to send event: ", event, data)
    for queue in sse_clients:
        print("sending to sse client!")
        await queue.put({"event": event, "data": data})

@router.post("/chat/send")
async def send_message(request: Request):
    form_data = await request.form()
    message = form_data.get("message")
    print(form_data)
    message_html = f'''
        <div class="flex items-start mb-2">
            <img src="var(--user-avatar)" alt="User Avatar" class="w-8 h-8 rounded-full mr-2">
            <div class="bg-gray-800 rounded-theme p-theme">
                <p class="text-secondary text-base">User: {message}</p>
            </div>
        </div>
    '''

    await send_event_to_clients("new_message", {"html": message_html})

    async def send_assistant_response(cmd, assistant_message):
        assistant_message_html = f'''
            <div class="flex items-start mb-2">
                <img src="var(--assistant-avatar)" alt="Assistant Avatar" class="w-8 h-8 rounded-full mr-2">
                <div class="bg-primary rounded-theme p-theme">
                    <p class="text-white text-base">Assistant: {assistant_message}</p>
                </div>
            </div>
        '''
        await send_event_to_clients("new_message", {"html": assistant_message_html})

    messages = [ { "role": "user", "content": message}]
    print("First messages: ", messages)
    await agent.chat_commands("phi3", messages=messages, cmd_callback=send_assistant_response)

    return {"status": "ok"}

@router.get("/", response_class=HTMLResponse)
async def get_chat_html():
    with open("static/chat.html", "r") as file:
        chat_html = file.read()
    return chat_html
