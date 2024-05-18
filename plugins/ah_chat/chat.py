from fastapi import APIRouter, Request
import traceback
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from .chatlog import ChatLog
from ..ah_agent import agent
from ..commands import command, command_manager
from ..services import service, service_manager
from ..hooks import hook, hook_manager
import asyncio
import os
import json
import nanoid

router = APIRouter()

if os.environ.get('AH_DEFAULT_LLM'):
    current_model = os.environ.get('AH_DEFAULT_LLM')
else:
    current_model = 'llama3'


class Message(BaseModel):
    message: str

sse_clients = set()

@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    print("chat_log = ", log_id)
    chat_log = ChatLog()
    chat_log.load_log(log_id)
    agent_ = agent.Agent(persona=chat_log.persona, clear_model=True)
    await asyncio.sleep(0.65)
    asyncio.create_task(hook_manager.warmup())

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

@service(is_local=True)
async def agent_output(event: str, data: dict, context=None):
    print("Try to send event: ", event, data)
    for queue in sse_clients:
        print("sending to sse client!")
        await queue.put({"event": event, "data": data})


@service(is_local=True)
async def partial_command(command: str, chunk: str, so_far: str, context=None):
    print("*** partial_command service call ***")
    print(command, chunk, so_far)
    persona_ = context.persona
    assistant_avatar = f"static/personas/{persona_['name']}/avatar.png"
    output = ''
    if not context.response_started:
        output = f'''
            <img src="{assistant_avatar}" alt="Assistant Avatar" class="w-8 h-8 rounded-full mr-2 inline-block">'''
    context.response_started = True
    output += f"<span>{chunk}</span>"
    await context.agent_output("new_message", output)


@router.put("/chat/{log_id}/{persona_name}")
async def init_chat(log_id: str, persona_name: str):
    chat_log = ChatLog(persona=persona_name)
    chat_log.save_log(log_id)
    persona_ = await service_manager.get_persona_data(persona_name)

class ChatContext:
    def __init__(self, command_manager, service_manager):
        self.command_manager = command_manager
        self.service_manager = service_manager
        self._commands = command_manager.functions
        self._services = service_manager.functions
        self.response_started = False

    def __getattr__(self, name):
        if name in self.__dict__ or name in self.__class__.__dict__:
            return super().__getattr__(name)

        if name in self._services:
            self.service_manager.context = self
            return getattr(self.service_manager, name)

        if name in self._commands:
            self.command_manager.context = self
            return getattr(self.command_manager, name)


@service(is_local=True)
async def insert_image(image_url, context=None):                                                                                                                
    await context.agent_output("new_message", f"<img src='{image_url}' />")                                                                             


@router.post("/chat/{log_id}/send")
async def send_message(log_id: str, request: Request):
    print("log_id = ", log_id)
    chat_log = ChatLog()
    chat_log.load_log(log_id)
    persona_ = await service_manager.get_persona_data(chat_log.persona)
    form_data = await request.form()
    user_avatar = 'static/user.png'
    assistant_avatar = f"static/personas/{persona_['name']}/avatar.png"
    user_name = form_data.get("user_name")
    if user_name is None:
        user_name = os.environ.get("AH_USER_NAME")
    message = form_data.get("message")
    agent_ = agent.Agent(persona=persona_)

    message_html = f'''
            <div class="ml-6 w-2/3">
                <img src="{user_avatar}" alt="User Avatar" class="w-8 h-8 rounded-full">
                <span class="text-secondary text-base">{message}</span>
            </div>
    '''

    await agent_output("new_message", message_html)
    chat_log.add_message({"role": "user", "content": f"({user_name}): {message}"})


    @command(is_local=True)
    async def say(assistant_message, context=None):
        """
        Say something to the user or chat room.
        One sentence per command. If you want to say multiple sentences, use multiple commands.

        # Example
        
        [
            { "say": "Hello, user." },
            { "say": "How can I help you today?" }
        ]

        """
        assistant_message_html = f'''
            <div class="flex items-start mb-2">
                <img src="{assistant_avatar}" alt="Assistant Avatar" class="w-8 h-8 rounded-full mr-2">
                <div class="bg-primary">
                    <p class="text-white text-yellow text-base">{assistant_message}</p>
                </div>
            </div>
        '''
        #await context.agent_output("new_message", assistant_message_html)
        json_cmd = { "say": assistant_message }

        chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})

    try:
        context = ChatContext(command_manager, service_manager)
        context.chat_log = chat_log
        context.persona = persona_

        await agent_.chat_commands(current_model, context=context, messages=chat_log.get_recent())
        print('ok')
    except Exception as e:
        print("Found an error in agent output: ")
        print(e)
        print(traceback.format_exc())

    return {"status": "ok"}

@router.get("/{persona_name}", response_class=HTMLResponse)
async def get_chat_html(persona_name: str):
    log_id = nanoid.generate()
    chat_log = ChatLog(log_id=log_id, persona=persona_name)
    chat_log.save_log()

    with open("static/chat.html", "r") as file:
        chat_html = file.read()
        chat_html = chat_html.replace("{{CHAT_ID}}", log_id)
    return chat_html

