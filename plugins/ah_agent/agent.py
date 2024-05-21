import asyncio
import json
import os
from jinja2 import Template
from ..commands import command_manager
import partial_json_parser

def find_new_substring(s1, s2):
    if s1 in s2:
        return s2.replace(s1, '', 1)
    return s2

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
            #print("Unloading llm")
            #await use_ollama.unload(self.model)
            #await asyncio.sleep(0.3)
            context.chat_log.add_message({"role": "assistant", "content": json_cmd})

        command_manager.context = context
        # cmd_args might be a single arg like integer or string, or it may be an array, or an object/dict with named args
        if isinstance(cmd_args, list):
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
        stack = []
        in_string = False
        escape_next = False
        last_partial_args = None

        async for part in stream:
            chunk = part['message']['content']
            buffer += chunk
            try:
                original_buffer = buffer
                buffer = buffer.replace("}\n", "},\n")
                buffer = self.remove_braces(buffer)
                cmd_obj = json.loads(buffer)
                cmd_name = next(iter(cmd_obj))
                if isinstance(cmd_obj, list):
                    print('detected command list')
                    cmd_obj = cmd_obj[0]
                    cmd_name = next(iter(cmd_obj)) 
                cmd_args = cmd_obj[cmd_name]
                result = await self.handle_cmds(cmd_name, cmd_args, json_cmd=buffer, context=context)
                results.append({"cmd": cmd_name, "result": result})
                print('results=',results)
                buffer = ""
                last_partial_args = None
            except json.JSONDecodeError as e:
                print("error parsing ||", e, " ||")
                print(buffer)
                buffer = original_buffer
                try:
                    partial = partial_json_parser.loads(buffer)
                    print("partial command found:", partial)
                    partial_command = next(iter(partial))
                    if partial_command is not None:
                        partial_args = partial[partial_command]
                        if isinstance(partial_args, str) and last_partial_args is not None:
                            diff_str = find_new_substring(last_partial_args, partial_args)
                        else:
                            diff_str = partial_args
                        print("sending partial command diff")
                        await context.partial_command(partial_command, diff_str, partial_args)
                        last_partial_args = partial_args
                except Exception as e:
                    print("error parsing partial command:", e)
                    pass

        return results

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

        return await self.parse_cmd_stream(stream, context)


