import asyncio
import json
from ..ah_ollama import use_ollama 
import os
from jinja2 import Template

class Agent:

    __init__(self, model=None, sys_core_template=None, persona=None, commands=[]):
        if model is None:
            if os.environ.get('AH_DEFAULT_LLM_MODEL'):
                self.model = os.environ.get('AH_DEFAULT_LLM_MODEL')
            else:
                self.model = 'llama3'
        else:
            self.model = model

        if sys_core is None:
            with open("system.j2", "r") as f:
                self.sys_core_template = f.read()
            else:
                self.sys_core_template = sys_core_template

        self.sys_template = Template(markdown_template)
 
        self.cmd_handler = {}

    def use_model(self, model_id, local=True):
        self.current_model = model_id

    async def set_cmd_handler(self, cmd_name, callback):
        self.cmd_handler[cmd_name] = callback
        print("recorded handler for ", cmd_name)

    async def unload_llm_if_needed(self):
        await use_ollama.unload(self.model)
        await asyncio.sleep(1)

    async def handle_cmds(self, cmd_name, cmd_args):
        print(f"Command: {cmd_name}")
        print(f"Arguments: {cmd_args}")
        print('----------------------------------')
        if cmd_name != 'say':
            print("Unloading llm")
            await use_ollama.unload('llama3')
            await asyncio.sleep(1)

        if cmd_name in self.cmd_handler:
            await cmd_handler[cmd_name](cmd_args)
        else:
            print(f"No handler for command {cmd_name}") 
            raise Exception(f"No handler for command {cmd_name}")

    def remove_braces(self, buffer):
        if buffer.endswith("\n"):
            buffer = buffer[:-1]
        if buffer.startswith('[ '):
            buffer = buffer[2:]
        if buffer.endswith(','):
            buffer = buffer[:-1]
        if buffer.endswith(']'):
            buffer = buffer[:-1]
        if buffer.startswith('['):
            buffer = buffer[1:]
        if buffer.endswith('},'):
            buffer = buffer[:-1]
        return buffer 

    async def parse_cmd_stream(self, stream):
        buffer = ""
        stack = []
        in_string = False
        escape_next = False

        async for part in stream:
            chunk = part['message']['content']
            buffer += chunk

            for char in chunk:
                if char == '"' and not escape_next:
                    in_string = not in_string
                elif char == '\\' and in_string:
                    escape_next = True
                elif char == '{' and not in_string:
                    stack.append(char)
                elif char == '}' and not in_string:
                    if stack and stack[-1] == '{':
                        stack.pop()
                        if not stack:
                            try:
                                buffer = self.remove_braces(buffer)
                                cmd_obj = json.loads(buffer)
                                cmd_name = next(iter(cmd_obj))
                                if isinstance(cmd_obj, list):
                                    print('detected command list')
                                    cmd_obj = cmd_obj[0]
                                    cmd_name = next(iter(cmd_obj)) 
                                cmd_args = cmd_obj[cmd_name]
                                await self.handle_cmds(cmd_name, cmd_args)
                                buffer = ""
                            except json.JSONDecodeError as e:
                                print("error parsing", e)
                                print(buffer)
                                pass

                escape_next = False

        if buffer:
            try:
                cmds = json.loads(buffer)
                for cmd_obj in cmds:
                    cmd_name = next(iter(cmd_obj))
                    cmd_args = cmd_obj[cmd_name]
                    await self.handle_cmds(cmd_name, cmd_args)
            except json.JSONDecodeError:
                print("error parsing")


    def render_system_msg(self):
       self.system_message = self.sys_template.render(self)
        return self.system_message

    async def chat_commands(self, model, cmd_callback=handle_cmds,
                            temperature=0, max_tokens=512, messages=[]):

        messages = [{"role": "system", "content": self.render_system_msg()}] + messages
        print("Messages:", messages, flush=True)

        stream = await use_ollama.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=messages)

        await self.parse_cmd_stream(stream, cmd_callback)


