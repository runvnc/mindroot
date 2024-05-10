from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from ..ah_agent import agent
from ..ah_sd import sd
from ..ah_faceswap import face_swap
import asyncio
import os

router = APIRouter()

if os.environ.get('AH_DEFAULT_LLM'):
    current_model = os.environ.get('AH_DEFAULT_LLM')
else:
    current_model = 'phi3'


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


async def return_image(prompt):
    result = await sd.simple_image(prompt)
    await send_event_to_clients("new_message", result)

async def face_swapped_image(prompt):
    img = await sd.simple_image(prompt, wrap=False)
    print("completed image out, about to swap. img = ", img, "face ref dir =", os.environ.get("AH_FACE_REF_DIR"))
    new_img = face_swap.face_swap(os.environ.get('AH_FACE_REF_DIR'), img, skip_nsfw=True, wrap_html=True)
    print("new_img:", new_img)
    await send_event_to_clients("new_message", new_img)


@router.post("/chat/send")
async def send_message(request: Request):
    form_data = await request.form()
    user_avatar = 'static/user.png'
    assistant_avatar = 'static/assistant.png'
    message = form_data.get("message")
    print(form_data)
    message_html = f'''
        <div class="flex items-start mb-2">
            <img src="{user_avatar}" alt="User Avatar" class="w-8 h-8 rounded-full mr-2">
            <div class="text-white">
                <p class="text-secondary text-base">{message}</p>
            </div>
        </div>
    '''

    await send_event_to_clients("new_message", message_html)

    async def send_assistant_response(assistant_message):
        assistant_message_html = f'''
            <div class="flex items-start mb-2">
                <img src="{assistant_avatar}" alt="Assistant Avatar" class="w-8 h-8 rounded-full mr-2">
                <div class="bg-primary">
                    <p class="text-white text-yellow text-base">{assistant_message}</p>
                </div>
            </div>
        '''
        await send_event_to_clients("new_message", assistant_message_html)

    messages = [ { "role": "user", "content": message}]
    print("First messages: ", messages)
    await agent.handle_cmd('say', send_assistant_response)
    await agent.handle_cmd('image', face_swapped_image)

    try:
        await agent.chat_commands(current_model, messages=messages)
    except Exception as e:
        print("Found an error in agent output: ")
        print(e)
        #messages.append({"role": "assistant", "content": str(e)})
        #messages.append({"role": "user", "content": "Invalid command or output format."})
        #print()
        #print()
        #print(messages)
        #await agent.chat_commands(current_model, messages=messages) 

    return {"status": "ok"}

@router.get("/", response_class=HTMLResponse)
async def get_chat_html():
    with open("static/chat.html", "r") as file:
        chat_html = file.read()
    return chat_html
