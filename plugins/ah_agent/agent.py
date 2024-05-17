import asyncio
import json
import os
from jinja2 import Template
from ..commands import command_manager

class Agent:

    def __init__(self, model=None, sys_core_template=None, persona=None, clear_model=False, commands=[]):
        if model is None:
            if os.environ.get('AH_DEFAULT_LLM'):
                self.model = os.environ.get('AH_DEFAULT_LLM')
            else:
                self.model = 'llama3'
        else:
            self.model = model

        self.persona = persona

        if sys_core_template is None:
            system_template_path = os.path.join(os.path.dirname(__file__), "system.j2")
            with open(system_template_path, "r") as f:
                self.sys_core_template = f.read()
        else:
            self.sys_core_template = sys_core_template

        self.sys_template = Template(self.sys_core_template)
 
        self.cmd_handler = {}
        
        #if clear_model:
        #    asyncio.create_task(use_ollama.unload(self.model))

    def use_model(self, model_id, local=True):
        self.current_model = model_id

    async def set_cmd_handler(self, cmd_name, callback):
        self.cmd_handler[cmd_name] = callback
        print("recorded handler for ", cmd_name)

    async def unload_llm_if_needed(self):
        print("not unloading llm")
        #await use_ollama.unload(self.model)
        #await asyncio.sleep(1)

    async def handle_cmds(self, cmd_name, cmd_args, json_cmd=None, context=None):
        print(f"Command: {cmd_name}")
        print(f"Arguments: {cmd_args}")
        print("Context:", context)
        print('----------------------------------')
        if cmd_name != 'say':
            print("Unloading llm")
            #await use_ollama.unload(self.model)
            #await asyncio.sleep(0.3)
            context.chat_log.add_message({"role": "assistant", "content": json_cmd})

        command_manager.context = context
        await command_manager.execute(cmd_name, cmd_args, context=context)

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

    async def parse_cmd_stream(self, stream, context):
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
                        if not stack and buffer is not None and buffer != "":
                            try:
                                buffer = buffer.replace("}\n", "},\n")
                                buffer = self.remove_braces(buffer)
                                cmd_obj = json.loads(buffer)
                                cmd_name = next(iter(cmd_obj))
                                if isinstance(cmd_obj, list):
                                    print('detected command list')
                                    cmd_obj = cmd_obj[0]
                                    cmd_name = next(iter(cmd_obj)) 
                                cmd_args = cmd_obj[cmd_name]
                                await self.handle_cmds(cmd_name, cmd_args, json_cmd=buffer, context=context)
                                buffer = ""
                            except json.JSONDecodeError as e:
                                print("error parsing ||", e, " ||")
                                print(buffer)
                                pass

                escape_next = False

        if buffer:
            try:
                cmds = json.loads(buffer)
                for cmd_obj in cmds:
                    cmd_name = next(iter(cmd_obj))
                    cmd_args = cmd_obj[cmd_name]
                    await self.handle_cmds(cmd_name, cmd_args, json_cmd=buffer, context=context)
            except json.JSONDecodeError:
                print("error parsing")


    def render_system_msg(self):
        print("docstrings:")
        print(command_manager.get_some_docstrings(self.persona["commands"]))
        data = {
            "command_docs": command_manager.get_some_docstrings(self.persona["commands"]),
            "persona": self.persona
        }
        self.system_message = self.sys_template.render(data)
        return self.system_message

    async def chat_commands(self, model, context,
                            temperature=0, max_tokens=512, messages=[]):

        messages = [{"role": "system", "content": self.render_system_msg()}] + messages
        print("Messages:", messages, flush=True)

        stream = await context.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=messages)

        await self.parse_cmd_stream(stream, context)


