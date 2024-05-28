from fastapi import APIRouter
import traceback
from fastapi.responses import HTMLResponse, JSONResponse
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
        await queue.put({"event": event, "data": json.dumps(data)})


@service(is_local=True)
async def partial_command(command: str, chunk: str, so_far: str, context=None):
    print("*** partial_command service call ***")
    persona_ = context.persona

    await context.agent_output("partial_command", { "command": command, "chunk": chunk,
                                                    "so_far": so_far, "persona": persona_['name'] })


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
        self.uncensored = False
        
        self.data = {}
        self.data['current_dir'] = 'data/users/default'

        if os.environ.get("AH_UNCENSORED"):
            self.uncensored = True

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
    await context.agent_output("image", {"url": image_url})


@router.post("/chat/{log_id}/send")
async def send_message(log_id: str, message_data: Message):
    print("log_id = ", log_id)
    chat_log = ChatLog()
    chat_log.load_log(log_id)
    persona_ = await service_manager.get_persona_data(chat_log.persona)
    # form_data = await request.form()
    user_avatar = 'static/user.png'
    assistant_avatar = f"static/personas/{persona_['name']}/avatar.png"
    user_name = os.environ.get("AH_USER_NAME")
    message = message_data.message
    agent_ = agent.Agent(persona=persona_)

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
        await context.agent_output("new_message", {"content": assistant_message,
                                                "persona": persona_['name'] })
        json_cmd = { "say": assistant_message }

        chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})
    context = ChatContext(command_manager, service_manager)
    context.chat_log = chat_log
    context.persona = persona_

    continue_processing = True
    while continue_processing:
        continue_processing = False
        try:
            results = await agent_.chat_commands(current_model, context=context, messages=chat_log.get_recent())
            out_results = []
            for result in results:
                if result['result'] is not None:
                    out_results.append(result)
                    continue_processing = True
            if continue_processing:
                chat_log.add_message({"role": "user", "content": "[SYSTEM]:\n\n" + json.dumps(out_results, indent=4)})
        except Exception as e:
            print("Found an error in agent output: ")
            print(e)
            print(traceback.format_exc())

    return {"status": "ok"}


@command(is_local=True)
async def json_encoded_md(json_encoded_markdown_text, context=None):
    """
    Output some markdown text to the user or chat room.
    Use this for any somewhat longer text that the user can read and
    and doesn't necessarily need to be spoken out loud.

    You can write as much text/sentences etc. as you need.

    IMPORTANT: make sure everything is properly encoded as this is a JSON 
    command (such as escaping double quotes, escaping newlines, etc.)

    Parameters:

    json_encoded_markdown_text - String.  MUST BE PROPERLY JSON-encoded string.

# Example

    [
        { "json_encoded_md": "## Section 1\\n\\n- item 1\\n- item 2" }
    ]

# Example

    [
        { "json_encoded_md": "Here is a list:\\n\\n- item 1\\n- item 2\\n- line 3" }
    ]


NOTICE THAT THE PARAMETER IS A JSON-ENCODED STRING WITH NO NEWLINES AND ONLY
PROPERLY ESCAPED TEXT.

    """
    await context.agent_output("new_message", {"content": json_encoded_markdown_text,
                                            "persona": context.persona['name'] })
    json_cmd = { "json_encoded_md": json_encoded_markdown_text }

    context.chat_log.add_message({"role": "assistant", "content": json.dumps(json_cmd)})


@router.get("/{persona_name}", response_class=HTMLResponse)
async def get_chat_html(persona_name: str):
    log_id = nanoid.generate()
    chat_log = ChatLog(log_id=log_id, persona=persona_name)
    chat_log.save_log()

    with open("static/chat.html", "r") as file:
        chat_html = file.read()
        chat_html = chat_html.replace("{{CHAT_ID}}", log_id)
    return chat_html

