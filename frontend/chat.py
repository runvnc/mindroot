from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import asyncio

app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="public")

class Message(BaseModel):
    message: str

sse_clients = set()

@app.get("/chat/events")
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

@app.post("/chat/send")
async def send_message(request: Request):
    form_data = await request.form()
    message = form_data.get("message")

    message_html = f'''
        <div class="flex items-start mb-2">
            <img src="var(--user-avatar)" alt="User Avatar" class="w-8 h-8 rounded-full mr-2">
            <div class="bg-gray-800 rounded-theme p-theme">
                <p class="text-secondary text-base">User: {message}</p>
            </div>
        </div>
    '''

    await send_event_to_clients("new_message", {"html": message_html})

    # Simulating assistant's response after 1 second
    async def send_assistant_response():
        await asyncio.sleep(1)
        assistant_message = "I am an AI assistant. How can I help you today?"
        assistant_message_html = f'''
            <div class="flex items-start mb-2">
                <img src="var(--assistant-avatar)" alt="Assistant Avatar" class="w-8 h-8 rounded-full mr-2">
                <div class="bg-primary rounded-theme p-theme">
                    <p class="text-white text-base">Assistant: {assistant_message}</p>
                </div>
            </div>
        '''
        await send_event_to_clients("new_message", {"html": assistant_message_html})

    asyncio.create_task(send_assistant_response())

    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def get_chat_html():
    with open("chat.html", "r") as file:
        chat_html = file.read()
    return chat_html
