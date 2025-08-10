import asyncio
import json
import os
import re
import json
from json import JSONDecodeError
from jinja2 import Template
from lib.providers.commands import command_manager, command
from lib.providers.hooks import hook_manager
from lib.pipelines.pipe import pipeline_manager
from lib.providers.services import service
from lib.providers.services import service_manager
from lib.json_str_block import replace_raw_blocks
import sys
from lib.utils.check_args import *
from .command_parser import parse_streaming_commands, invalid_start_format
from datetime import datetime
import pytz
import traceback
from lib.logging.logfiles import logger
from lib.utils.debug import debug_box
from .init_models import *
from lib.chatcontext import ChatContext
from .cmd_start_example import *
from lib.templates import render


error_result = """
[SYSTEM]: ERROR, invalid response format.

Your response does not appear to adhere to the command list format.

Common causes:

- replied with JSON inside of fenced code blocks instead of JSON or RAW string format as below

- ONLY if your model supports this, for complex multiline string arguments, use the RAW format described in system instructions, e.g.:

...

{ "json_encoded_md": { "markdown": START_RAW
The moon, so bright
It's shining light
Like a pizza pie
In the sky
END_RAW
} }

...

- iF your model does not support RAW format or it is not a complex multiline string like code, you MUST properly escape JSON strings!
  - remember newlines, double quotes, etc. must be escaped (but not double escaped)!

- plain text response before JSON.

- some JSON args with unescaped newlines, etc.

- multiple command lists. Only one command list response is allowed!
  - This is a frequent cause of parse errors.

- some characters escaped that did not need to be/invalid

Please adhere to the system JSON command list response format carefully.
"""

@service()
async def get_agent_data(agent_name, context=None):
    logger.info("Agent name: {agent_name}", agent_name=agent_name)

    agent_path = os.path.join('data/agents', 'local', agent_name)

    if not os.path.exists(agent_path):
        agent_path = os.path.join('data/agents', 'shared', agent_name)
        if not os.path.exists(agent_path):
            return {}
    agent_file = os.path.join(agent_path, 'agent.json')
    if not os.path.exists(agent_file):
        return {}
    with open(agent_file, 'r') as f:
        agent_data = json.load(f)

    # Ensure required_plugins is present
    if 'required_plugins' not in agent_data:
        agent_data['required_plugins'] = []

    try:
        agent_data["persona"] = await service_manager.get_persona_data(agent_data["persona"])
    except Exception as e:
        logger.error("Error getting persona data", extra={"error": str(e)})
        raise e

    agent_data["flags"] = agent_data["flags"]
    agent_data["flags"] = list(dict.fromkeys(agent_data["flags"]))
    return agent_data



def find_new_substring(s1, s2):
    if s1 in s2:
        return s2.replace(s1, '', 1)
    return s2

class Agent:

    def __init__(self, model=None, sys_core_template=None, agent=None, clear_model=False, commands=[], context=None):
        if model is None:
            if os.environ.get('AH_DEFAULT_LLM'):
                self.model = os.environ.get('AH_DEFAULT_LLM')
            else:
                self.model = 'llama3'
        else:
            self.model = model

        self.agent = agent

        #if sys_core_template is None:
        #    system_template_path = os.path.join(os.path.dirname(__file__), "system.j2")
        #    with open(system_template_path, "r") as f:
        #        self.sys_core_template = f.read()
        #else:
        #    self.sys_core_template = sys_core_template

        #self.sys_template = Template(self.sys_core_template)

        self.cmd_handler = {}
        self.context = context

        #if clear_model:
        #    logger.debug("Unloading model")
        #    asyncio.create_task(use_ollama.unload(self.model))

    def use_model(self, model_id, local=True):
        self.current_model = model_id

    async def set_cmd_handler(self, cmd_name, callback):
        self.cmd_handler[cmd_name] = callback
        logger.info("Recorded handler for command: {command}", command=cmd_name)

    async def unload_llm_if_needed(self):
        logger.info("Not unloading LLM")
        #await use_ollama.unload(self.model)
        #await asyncio.sleep(1)

    async def handle_cmds(self, cmd_name, cmd_args, json_cmd=None, context=None):
        if 'finished_conversation' in context.data and context.data['finished_conversation']:
            logger.warning("Conversation is finished, not executing command")
            print("\033[91mConversation is finished, not executing command\033[0m")
            return None

        logger.info("Command execution: {command}", command=cmd_name)
        logger.debug("Command details: {details}", details={
            "command": cmd_name,
            "arguments": cmd_args,
            "context": str(context)
        })
        context.chat_log.add_message({"role": "assistant", "content": [{"type": "text", 
                                                                       "text": '['+json_cmd+']' }]})
        command_manager.context = context

        if cmd_name == "reasoning":
            return None

        # cmd_args might be a single arg like integer or string, or it may be an array, or an object/dict with named args
        try:
            if isinstance(cmd_args, list):
                #filter out empty strings
                cmd_args = [x for x in cmd_args if x != '']
                logger.debug("Executing command with list arguments", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args)
                logger.debug("Executing command with list arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, *cmd_args)
            elif isinstance(cmd_args, dict):
                logger.debug("Executing command with dict arguments", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args)
                logger.debug("Executing command with dict arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, **cmd_args)
            else:
                logger.debug("Executing command with single argument", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args)
                logger.debug("Executing command with single argument", extra={"step": 2})
                return await command_manager.execute(cmd_name, cmd_args)

        except Exception as e:
            trace = traceback.format_exc()
            print("\033[96mError in handle_cmds: " + str(e) + "\033[0m")
            print("\033[96m" + trace + "\033[0m")
            logger.error("Error in handle_cmds", extra={
                "error": str(e),
                "command": cmd_name,
                "arguments": cmd_args,
                "traceback": trace
            })

            return {"error": str(e)}

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

    async def parse_single_cmd(self, json_str, context, buffer, match=None):
        cmd_name = '?'
        try:
            cmd_obj = json.loads(json_str)
            cmd_name = next(iter(cmd_obj))
            if isinstance(cmd_obj, list):
                cmd_obj = cmd_obj[0]
                cmd_name = next(iter(cmd_obj))

            cmd_args = cmd_obj[cmd_name]
            # make sure that cmd_name is in self.agent["commands"]
            if cmd_name not in self.agent["commands"]:
                logger.warning("Command not found in agent commands", extra={"command": cmd_name})
                return None, buffer
            if check_empty_args(cmd_args):
                logger.info("Empty arguments for command", extra={"command": cmd_name})
                return None, buffer
            else:
                logger.info("Non-empty arguments for command", extra={"command": cmd_name, "arguments": cmd_args})
            # Handle the full command
            result = await self.handle_cmds(cmd_name, cmd_args, json_cmd=json_str, context=context)
            await context.command_result(cmd_name, result)

            cmd = {"cmd": cmd_name, "result": result}
            # Remove the processed JSON object from the buffer
            if match is not None:
                buffer = buffer[match.end():]
                buffer = buffer.lstrip(',').rstrip(',')
            return [cmd], buffer
        except Exception as e:
            trace = traceback.format_exc()
            logger.error("Error processing command", extra={"error": str(e) + "\n\n" + trace})

            json_str = '[' + json_str + ']'

            return None, buffer


    async def parse_cmd_stream(self, stream, context):
        buffer = ""
        results = []
        full_cmds = []

        num_processed = 0
        parse_failed = False
        debug_box("Parsing command stream")
        debug_box(str(context))
        original_buffer = ""

        async for part in stream:
            buffer += part
            original_buffer += part

            logger.debug(f"Current buffer: ||{buffer}||")
       
            if invalid_start_format(buffer):
                print("Found invalid start to buffer", buffer)
                context.chat_log.add_message({"role": "assistant", "content": buffer})
                started_with = f"Your invalid command started with: {buffer[0:20]}"
                results.append({"cmd": "UNKNOWN", "args": { "invalid": "(" }, "result": error_result + "\n\n" + started_with})
                return results, full_cmds 

            if len(buffer) > 0 and buffer[0] == '{':
                buffer = "[" + buffer

            # happened with Qwen 3 for some reason
            buffer = buffer.replace('}] <>\n\n[{','}, {')
            buffer = buffer.replace('}] <>\n[{','}, {')

            commands, partial_cmd = parse_streaming_commands(buffer)

            if isinstance(commands, int):
                continue

            if not isinstance(commands, list):
                commands = [commands]

            try:
                if len(commands) == 1 and 'commands' in commands[0]:
                    commands = commands[0]['commands']
            except Exception as e:
                continue

            logger.debug(f"commands: {commands}, partial_cmd: {partial_cmd}")

            if 'finished_conversation' in context.data and context.data['finished_conversation']:
                logger.warning("Conversation is finished or halted, exiting stream parsing")
                debug_box(f"""Conversation is finished or halted, exiting stream""")
                debug_box(str(context))
                # stream is actually a generator
                if partial_cmd is not None:
                    cmd_name = next(iter(partial_cmd))
                    if cmd_name in ["say", "json_encoded_md", "think"]:
                        context.chat_log.add_message({"role": "assistant", "content": str(partial_cmd[cmd_name])})
                    else:
                        context.chat_log.add_message({"role": "assistant", "content": str(partial_cmd) + "(Interrupted)"})
                try:
                    stream.close()
                except Exception as e:
                    print("\033[91mError closing stream\033[0m")

                return results, full_cmds


            if len(commands) > num_processed:
                logger.debug("New command(s) found")
                logger.debug(f"Commands: {commands}")
                for i in range(num_processed, len(commands)):
                    try:
                        cmd = commands[i]
                        try:
                            cmd_name = next(iter(cmd))
                        except Exception as e:
                            print("next iter failed. cmd is")
                            print(cmd)
                            break
                        if isinstance(cmd, str):
                            print("\033[91m" + "Invalid command format, expected object, trying to parse anyway" + "\033[0m")
                            print("\033[91m" + str(cmd) + "\033[0m")
                            cmd = json.loads(cmd)
                            cmd_name = next(iter(cmd))
                        cmd_args = cmd[cmd_name]
                        logger.debug(f"Processing command: {cmd}")
                        await context.partial_command(cmd_name, json.dumps(cmd_args), cmd_args)

                        result = await self.handle_cmds(cmd_name, cmd_args, json_cmd=json.dumps(cmd), context=context)
                        await context.command_result(cmd_name, result)
                        sys_header = "Note: tool command results follow, not user replies" 
                        sys_header = ""
                        full_cmds.append({ "SYSTEM": sys_header, "cmd": cmd_name, "args": cmd_args, "result": result})
                        if result is not None:
                            results.append({"SYSTEM": sys_header, "cmd": cmd_name, "args": { "omitted": "(see command msg.)"}, "result": result})

                        num_processed = len(commands)
                    except Exception as e:
                        trace = traceback.format_exc()
                        logger.error(f"Error processing command: {e} \n{trace}")
                        logger.error(str(e))
                        pass
            else:
                logger.debug("No new commands found")
                # sometimes partial_cmd is actually a string for some reason
                # definitely skip that
                # check if partial_cmd is a string
                is_string = isinstance(partial_cmd, str)
                if partial_cmd is not None and partial_cmd != {} and not is_string:
                    logger.debug(f"Partial command {partial_cmd}")
                    try:
                        cmd_name = next(iter(partial_cmd))
                        cmd_args = partial_cmd[cmd_name]
                        logger.debug(f"Partial command detected: {partial_cmd}")
                        await context.partial_command(cmd_name, json.dumps(cmd_args), cmd_args)
                    except Exception as de:
                        logger.error("Failed to parse partial command")
                        logger.error(str(de))
                        pass

        #print("\033[92m" + str(full_cmds) + "\033[0m")
        # getting false positive on this check
        reasonOnly = False
        try:
            cmd_name = next(iter(full_cmds[0]))
            if cmd_name == 'reasoning':
                reasonOnly = True
                for cmd in full_cmds:
                    if cmd_name != 'reasoning':
                        reasonOnly = False
                        break
        except Exception as e:
            pass
        if len(full_cmds) == 0 or reasonOnly:
            print("\033[91m" + "No results and parse failed" + "\033[0m")
            try:
                buffer = replace_raw_blocks(buffer)
                parse_ok = json.loads(buffer)
                parse_fail_reason = ""
                tried_to_parse = ""
            except JSONDecodeError as e:
                print("final parse fail")
                print(buffer)
                parse_fail_reason = str(e)
                context.chat_log.add_message({"role": "assistant", "content": buffer})
                print(parse_fail_reason)
                await asyncio.sleep(1)
                tried_to_parse = f"\n\nTried to parse the following input: {original_buffer}"
            results.append({"cmd": "UNKNOWN", "args": { "invalid": "("}, "result": error_result + '\n\nJSON parse error was: ' + parse_fail_reason +
                             tried_to_parse })
 
        return results, full_cmds

    async def render_system_msg(self):
        logger.debug("Docstrings:")
        logger.debug(command_manager.get_some_docstrings(self.agent["commands"]))
        now = datetime.now()

        formatted_time = now.strftime("~ %Y-%m-%d %I %p %Z%z")

        data = {
            "command_docs": command_manager.get_some_docstrings(self.agent["commands"]),
            "agent": self.agent,
            "persona": self.agent['persona'],
            "formatted_datetime": formatted_time,
            "context_data": self.context.data
        }
        # is say in the command_manager
        if 'say' in command_manager.functions.keys():
            print("I found say! in the functions!")
        else:
            print("Say is not in the functions!")
        if 'say' in data['command_docs'].keys():
            print("I found say in the command docs!")
    
        # we need to be doubly sure to remove anything from command_docs that is not in command_manager.functions.keys()
        for cmd in data['command_docs']:
            if cmd not in command_manager.functions.keys():
                print("Removing " + cmd + " from command_docs")
                del data['command_docs'][cmd]

        #self.system_message = self.sys_template.render(data)
        self.system_message = await render('system', data)
 
        additional_instructions = await hook_manager.add_instructions(self.context)

        for instruction in additional_instructions:
            self.system_message += instruction + "\n\n"

        return self.system_message


    async def chat_commands(self, model, context,
                            temperature=0, max_tokens=4000, messages=[]):

        self.context = context
        content = [ { "type": "text", "text": await self.render_system_msg() } ]
        messages = [{"role": "system", "content": content }] + demo_boot_msgs() + messages

        #logger.info("Messages for chat", extra={"messages": messages})

        json_messages = json.dumps(messages)
        new_messages = json.loads(json_messages)

        if os.environ.get("AH_DEFAULT_MAX_TOKENS"):
            max_tokens = int(os.environ.get("AH_DEFAULT_MAX_TOKENS"))
        try:
            tmp_data = { "messages": new_messages }
            debug_box("Filtering messages")
            #debug_box(tmp_data)
            tmp_data = await pipeline_manager.filter_messages(tmp_data, context=context)
            new_messages = tmp_data['messages']
        except Exception as e:
            logger.error("Error filtering messages")
            logger.error(str(e))

        if new_messages[0]['role'] != 'system':
            logger.error("First message is not a system message")
            print("\033[91mFirst message is not a system message\033[0m")
            return None, None

        if not isinstance(context.agent, dict):
            context.agent = await get_agent_data(context.agent, context=context)

        if model is None:
            if 'service_models' in context.agent and context.agent['service_models'] is not None:
                if context.agent['service_models'].get('stream_chat', None) is None:
                    model = os.environ.get("DEFAULT_LLM_MODEL")

        stream = await context.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=new_messages,
                                        context=context)

        ret, full_cmds = await self.parse_cmd_stream(stream, context)
        logger.debug("System message was:")
        logger.debug(await self.render_system_msg())

        # use green text
        print("\033[92m" + "Just after stream chat, last two messages in chat log:")
        print("------------------------------------")
        print(context.chat_log.messages[-1])
        print(context.chat_log.messages[-2])
        # switch back to normal text
        print("\033[0m")

        return ret, full_cmds

@service()
async def run_command(cmd_name, cmd_args, context=None):
    if context is None:
        raise Exception("run_command: No context provided")
        
    agent = Agent(agent=context.agent)
    json_cmd = json.dumps({cmd_name: cmd_args})
    asyncio.create_task(agent.handle_cmds(cmd_name, cmd_args, json_cmd, context=context))

