import asyncio
import json
import os
import re
from jinja2 import Template
from ..commands import command_manager
from ..hooks import hook_manager
import partial_json_parser

def find_new_substring(s1, s2):
    if s1 in s2:
        return s2.replace(s1, '', 1)
    return s2

class Agent:

    def __init__(self, model=None, sys_core_template=None, persona=None, clear_model=False, commands=[], context=None):
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
        self.context = context

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
            #print("Unloading llm")
            #await use_ollama.unload(self.model)
            #await asyncio.sleep(0.3)
            context.chat_log.add_message({"role": "assistant", "content": json_cmd})

        command_manager.context = context
        # cmd_args might be a single arg like integer or string, or it may be an array, or an object/dict with named args
        if isinstance(cmd_args, list):
            #filter out empty strings
            cmd_args = [x for x in cmd_args if x != '']
            return await command_manager.execute(cmd_name, *cmd_args, context=context)
        elif isinstance(cmd_args, dict):
            return await command_manager.execute(cmd_name, **cmd_args, context=context)
        else:
            return await command_manager.execute(cmd_name, cmd_args, context=context)

    def remove_braces(self, buffer):
        if buffer.endswith("\n"):
            buffer = buffer[:-1]
        if buffer.startswith('[ '):
            buffer = buffer[2:]
        if buffer.startswith(' ['):
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
        results = []
        last_partial_args = None

        async for part in stream:
            chunk = part
            buffer += chunk

            while buffer:
                # Check for full JSON command
                match = re.search(r'\{.*?\}', buffer)
                if match:
                    json_str = match.group(0)
                    cmd_obj = json.loads(json_str)
                    cmd_name = next(iter(cmd_obj))
                    if isinstance(cmd_obj, list):
                        cmd_obj = cmd_obj[0]
                        cmd_name = next(iter(cmd_obj))
                    cmd_args = cmd_obj[cmd_name]

                    # Handle the full command
                    result = await self.handle_cmds(cmd_name, cmd_args, json_cmd=json_str, context=context)
                    results.append({"cmd": cmd_name, "result": result})

                    # Remove the processed JSON object from the buffer
                    buffer = buffer[match.end():]
                    buffer = buffer.lstrip(',').rstrip(',')

                else:
                    # Attempt to parse partial JSON command
                    try:
                        partial = partial_json_parser.loads(buffer)
                        if isinstance(partial, list):
                            partial = partial[0]

                        partial_command = next(iter(partial))
                        if partial_command is not None:
                            partial_args = partial[partial_command]
                            if isinstance(partial_args, str) and last_partial_args is not None:
                                diff_str = find_new_substring(last_partial_args, partial_args)
                            else:
                                diff_str = json.dumps(partial_args)
                            await context.partial_command(partial_command, diff_str, partial_args)
                            last_partial_args = partial_args
                    except Exception as e:
                        print("error parsing partial command:", e)
                        break

        return results

    async def render_system_msg(self):
        print("docstrings:")
        print(command_manager.get_some_docstrings(self.persona["commands"]))
        data = {
            "command_docs": command_manager.get_some_docstrings(self.persona["commands"]),
            "persona": self.persona
        }
        self.system_message = self.sys_template.render(data)
        additional_instructions = await hook_manager.add_instructions(self.context)
        for instruction in additional_instructions:
            self.system_message += instruction + "\n\n"

        return self.system_message

    async def chat_commands(self, model, context,
                            temperature=0, max_tokens=512, messages=[]):

        self.context = context
        messages = [{"role": "system", "content": await self.render_system_msg()}] + messages
        print("Messages:", messages, flush=True)
        
        stream = await context.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=messages)

        ret = await self.parse_cmd_stream(stream, context)
        print("system message was:")
        print(self.render_system_msg())
        return ret
