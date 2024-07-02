import asyncio
import json
import os
import re
import json
from json import JSONDecodeError
from jinja2 import Template
from ..commands import command_manager
from ..hooks import hook_manager
from ..services import service 
from ..services import service_manager
import sys
from ..check_args import *
from ..ah_agent.command_parser import parse_streaming_commands

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

    agent_data["persona"] = await service_manager.get_persona_data(agent_data["persona"])
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
        logger.info("Recorded handler for command: {command}", command=cmd_name)

    async def unload_llm_if_needed(self):
        logger.info("Not unloading LLM")
        #await use_ollama.unload(self.model)
        #await asyncio.sleep(1)

    async def handle_cmds(self, cmd_name, cmd_args, json_cmd=None, context=None):
        logger.info("Command execution: {command}", command=cmd_name)
        logger.debug("Command details: {details}", details={
            "command": cmd_name,
            "arguments": cmd_args,
            "context": str(context)
        })
        #if cmd_name != 'say':
        #    #print("Unloading llm")
        #    #await use_ollama.unload(self.model)
        #    #await asyncio.sleep(0.3)
        context.chat_log.add_message({"role": "assistant", "content": '['+json_cmd+']' })

        command_manager.context = context
        # cmd_args might be a single arg like integer or string, or it may be an array, or an object/dict with named args
        try:
            if isinstance(cmd_args, list):
                #filter out empty strings
                cmd_args = [x for x in cmd_args if x != '']
                logger.debug("Executing command with list arguments", extra={"step": 1})
                await context.running_command(cmd_name)
                logger.debug("Executing command with list arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, *cmd_args)
            elif isinstance(cmd_args, dict):
                logger.debug("Executing command with dict arguments", extra={"step": 1})
                await context.running_command(cmd_name)
                logger.debug("Executing command with dict arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, **cmd_args)
            else:
                logger.debug("Executing command with single argument", extra={"step": 1})
                await context.running_command(cmd_name)
                logger.debug("Executing command with single argument", extra={"step": 2})
                return await command_manager.execute(cmd_name, cmd_args)

        except Exception as e:
            logger.error("Error in handle_cmds", extra={
                "error": str(e),
                "command": cmd_name,
                "arguments": cmd_args
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
            logger.error("Error processing command", extra={"error": str(e)})

            json_str = '[' + json_str + ']'
            
            return None, buffer


    async def parse_cmd_stream(self, stream, context):
        buffer = ""
        results = []

        num_processed = 0

        async for part in stream:
            buffer += part
            #print(f"Current buffer: ||{buffer}||")
            
            commands, partial_cmd = parse_streaming_commands(buffer)
            if not isinstance(commands, list):
                commands = [commands]

            #print("commands: ", commands, "partial_cmd:", partial_cmd)

            if len(commands) > num_processed:
                #print("New command(s) found")
                for i in range(num_processed, len(commands)):
                    try:
                        cmd = commands[i]
                        cmd_name = next(iter(cmd))
                        cmd_args = cmd[cmd_name]
                        #print(f"Processing command: {cmd}")
                        result = await self.handle_cmds(cmd_name, cmd_args, json_cmd=json.dumps(cmd), context=context)
                        await context.command_result(cmd_name, result)
                        results.append({"cmd": cmd_name, "result": result})
                        num_processed = len(commands)
                    except Exception as e:
                        #print("Error processing command:", e)
                        #print(e)
                        pass
            else:
                #print("No new commands found")
                # check if not None or empty object                
                if partial_cmd is not None and partial_cmd != {}:
                    #print("Partial command", partial_cmd)
                    try:
                        cmd_name = next(iter(partial_cmd))
                        cmd_args = partial_cmd[cmd_name]
                        #print(f"Partial command detected: {partial_cmd}")
                        await context.partial_command(cmd_name, json.dumps(cmd_args), cmd_args)
                    except json.JSONDecodeError as de:
                        #print("failed to parse partial command")
                        #print(de)
                        pass

        return results

    async def render_system_msg(self):
        #print("docstrings:")
        #print(command_manager.get_some_docstrings(self.agent["commands"]))
        data = {
            "command_docs": command_manager.get_some_docstrings(self.agent["commands"]),
            "agent": self.agent,
            "persona": self.agent['persona']
        }
        self.system_message = self.sys_template.render(data)
        additional_instructions = await hook_manager.add_instructions(self.context)

        for instruction in additional_instructions:
            self.system_message += instruction + "\n\n"

        return self.system_message


    async def chat_commands(self, model, context,
                            temperature=0, max_tokens=4000, messages=[]):

        self.context = context
        messages = [{"role": "system", "content": await self.render_system_msg()}] + messages
        logger.info("Messages for chat", extra={"messages": messages})
        
        stream = await context.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=messages)

        ret = await self.parse_cmd_stream(stream, context)
        #print("system message was:")
        #print(await self.render_system_msg())
        return ret

from loguru import logger
