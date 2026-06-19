import asyncio
import json
import os
import re
import json
import time
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
import nanoid
from lib.xml_stream_events import XmlEventStream
from lib.xml_docstring_adapter import convert_docstring_json_examples_to_xml


def _truthy(val) -> bool:
    return str(val).lower() in ('1', 'true', 'yes', 'on')


def xml_streaming_enabled(context=None) -> bool:
    """Whether XML/raw-text command streaming is active for THIS agent/turn.

    Per-agent ONLY by default: the flag must be set in the agent's own env
    overrides (context.env['MR_XML_STREAMING'], populated from agent.json
    'env'). This deliberately does NOT honor a bare process-level
    MR_XML_STREAMING, because that would silently switch EVERY agent (including
    JSON/text agents and delegated mr_sip call children) into speak-everything
    XML mode and break them.

    Escape hatch for genuinely all-voice instances: set MR_XML_STREAMING_GLOBAL
    (process env) truthy to allow the process-level MR_XML_STREAMING fallback.
    """
    # 1) Per-agent override (authoritative).
    if context is not None:
        env = getattr(context, 'env', None)
        if isinstance(env, dict) and 'MR_XML_STREAMING' in env:
            return _truthy(env.get('MR_XML_STREAMING'))

    # 2) Opt-in process-wide fallback only when explicitly globalized.
    #    Read the RAW environ to avoid the context-aware shim resolving these
    #    from a nearby context.env (we already handled per-agent above).
    raw_env = os.environ
    try:
        from lib.context_environ import _original_environ as _raw
        if _raw is not None:
            raw_env = _raw
    except Exception:
        pass
    if _truthy(raw_env.get('MR_XML_STREAMING_GLOBAL', '')):
        return _truthy(raw_env.get('MR_XML_STREAMING', ''))
    return False


import logging
if os.environ.get('MR_DEBUG') == '1':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.CRITICAL)

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

# In-memory cache for agent data to avoid repeated disk reads
_agent_data_cache = {}

@service()
async def get_agent_data(agent_name, context=None):
    global _agent_data_cache
    # Return cached agent data if available
    if agent_name in _agent_data_cache:
        return _agent_data_cache[agent_name]


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
    # Cache the result
    _agent_data_cache[agent_name] = agent_data
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

    async def handle_cmds(self, cmd_name, cmd_args, json_cmd=None, context=None, cmd_id=None):
        # Check both permanent finish and temporary cancellation
        if context.data.get('cancel_current_turn'):
            logger.warning("Turn cancelled, not executing command")
            print("\033[91mTurn cancelled, not executing command\033[0m")
            raise asyncio.CancelledError("Turn cancelled")
        
        if context.data.get('finished_conversation'):
            logger.warning("Conversation finished, not executing command")
            print("\033[91mConversation finished, not executing command\033[0m")
            return None

        logger.info("Command execution: {command}", command=cmd_name)
        logger.debug("Command details: {details}", details={
            "command": cmd_name,
            "arguments": cmd_args,
            "context": str(context)
        })
        # When xml_streaming is active, store original output (not pipe-transformed JSON)
        # so the LLM sees its own XML format in future turns, not JSON
        xml_state = context.data.get('_xml_stream_state', {}) if context is not None else {}
        use_xml_original = (
            xml_state.get('mode') == 'xml' and context.data.get('_xml_original_buffer')
        )
        if use_xml_original:
            msg_content = context.data['_xml_original_buffer']
        else:
            msg_content = [{"type": "text", "text": '['+json_cmd+']' }]
        await context.chat_log.add_message_async({"role": "assistant", "content": msg_content})
        command_manager.context = context

        if cmd_name == "reasoning":
            return None

        # cmd_args might be a single arg like integer or string, or it may be an array, or an object/dict with named args
        try:
            if isinstance(cmd_args, list):
                #filter out empty strings
                cmd_args = [x for x in cmd_args if x != '']
                logger.debug("Executing command with list arguments", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
                logger.debug("Executing command with list arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, *cmd_args)
            elif isinstance(cmd_args, dict):
                logger.debug("Executing command with dict arguments", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
                logger.debug("Executing command with dict arguments", extra={"step": 2})
                return await command_manager.execute(cmd_name, **cmd_args)
            else:
                logger.debug("Executing command with single argument", extra={"step": 1})
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
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
        # Reset per-turn XML stream state so a new adapter is used each turn
        context.data.pop('_xml_stream_state', None)
        context.data.pop('_xml_original_buffer', None)
        full_cmds = []
        
        command_ids = {}  # Track command IDs: {command_index: command_id}
        num_processed = 0
        parse_failed = False
        debug_box("Parsing command stream")
        last_partial_emit_time = 0.0
        last_partial_emit_len = 0
        partial_min_interval = float(os.environ.get("MR_PARTIAL_COMMAND_MIN_INTERVAL", "0.05"))
        partial_min_chars = int(os.environ.get("MR_PARTIAL_COMMAND_MIN_CHARS", "256"))
        debug_box(str(context))
        original_buffer = ""

        async for part in stream:
            original_buffer += part

            # Store original buffer for xml_streaming mode (used by handle_cmds)
            context.data['_xml_original_buffer'] = original_buffer

            tmp_data = await pipeline_manager.process_stream({'chunk': part}, context=context)
            part = tmp_data.get('chunk', '')
            buffer += part

            # Give the web server/SSE machinery a chance to run during long streams.
            # The command parser below can be CPU-heavy on large partial JSON buffers.
            await asyncio.sleep(0)

            logger.debug(f"Current buffer: ||{buffer}||")
       
            if invalid_start_format(buffer):
                print("Found invalid start to buffer", buffer)
                # When xml_streaming is active, store original output (not pipe-transformed JSON)
                xml_state = context.data.get('_xml_stream_state', {})
                msg_content = original_buffer if xml_state.get('mode') == 'xml' else buffer
                await context.chat_log.add_message_async({"role": "assistant", "content": msg_content})
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

            # Check for cancellation (either permanent or current turn)
            if context.data.get('finished_conversation') or context.data.get('cancel_current_turn'):
                logger.warning("Conversation is finished or halted, exiting stream parsing")
                debug_box("Conversation is finished or halted, exiting stream")
                debug_box(str(context))
                
                # Add partial command to chat log if present
                if partial_cmd is not None:
                    cmd_name = next(iter(partial_cmd))
                    if cmd_name in ["say", "json_encoded_md", "think"]:
                        await context.chat_log.add_message_async({"role": "assistant", "content": str(partial_cmd[cmd_name])})
                    else:
                        await context.chat_log.add_message_async({"role": "assistant", "content": str(partial_cmd) + "(Interrupted)"})
                
                # Clear the temporary cancel flag so next turn can proceed
                if 'cancel_current_turn' in context.data:
                    del context.data['cancel_current_turn']
                    await context.save_context()
                
                try:
                    stream.close()
                except Exception as e:
                    print("\033[91mError closing stream\033[0m")

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
                        
                        # Use existing ID if we have one, otherwise generate new
                        cmd_id = command_ids.get(i, nanoid.generate())
                        command_ids[i] = cmd_id
                        
                        logger.debug(f"Processing command: {cmd}")
                        await context.partial_command(cmd_name, json.dumps(cmd_args), cmd_args, cmd_id=cmd_id)
 
                        cmd_task = asyncio.create_task(
                            self.handle_cmds(cmd_name, cmd_args, json_cmd=json.dumps(cmd), context=context, cmd_id=cmd_id)
                        )
                        context.data['active_command_task'] = cmd_task
                        try:
                            result = await cmd_task
                        except asyncio.CancelledError:
                            raise  # Propagate cancellation up
                        finally:
                            # Clear the task from context once it's done or cancelled
                            if context.data.get('active_command_task') == cmd_task:
                                del context.data['active_command_task']

                        await context.command_result(cmd_name, result, cmd_id=cmd_id)
                        sys_header = "Note: tool command results follow, not user replies" 
                        sys_header = ""

                        if result == "SYSTEM: WARNING - Command interrupted!\n\n":
                            logger.warning("Command was interrupted. Stopping processing.")
                            await context.chat_log.drop_last('assistant')
                            await asyncio.sleep(0.5)
                            break
                            return results, full_cmds


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
                        
                        # Use existing ID if we have one, otherwise generate new
                        cmd_id = command_ids.get(num_processed, nanoid.generate())
                        command_ids[num_processed] = cmd_id
                        
                        # Long streamed markdown/write/task_result commands can otherwise
                        # emit a full growing JSON payload on every provider token. That
                        # monopolizes the event loop and makes ordinary page requests stall.
                        now = time.monotonic()
                        approx_len = len(buffer)
                        should_emit = (
                            partial_min_interval <= 0
                            or (now - last_partial_emit_time) >= partial_min_interval
                            or (approx_len - last_partial_emit_len) >= partial_min_chars
                        )
                        if should_emit:
                            logger.debug(f"Partial command detected: {partial_cmd}")
                            await context.partial_command(cmd_name, json.dumps(cmd_args), cmd_args, cmd_id=cmd_id)
                            last_partial_emit_time = now
                            last_partial_emit_len = approx_len
                    except Exception as de:
                        logger.error("Failed to parse partial command")
                        logger.error(str(de))
                        pass

        # Flush any remaining XML-stream tool commands
        tmp_data = await pipeline_manager.process_stream({'chunk': '', 'finish': True}, context=context)
        if tmp_data.get('chunk'):
            buffer += tmp_data['chunk']

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
                # When xml_streaming is active, store original output (not pipe-transformed JSON)
                xml_state = context.data.get('_xml_stream_state', {})
                msg_content = original_buffer if xml_state.get('mode') == 'xml' else buffer
                await context.chat_log.add_message_async({"role": "assistant", "content": msg_content})
                print(parse_fail_reason)
                await asyncio.sleep(1)
                tried_to_parse = f"\n\nTried to parse the following input: {original_buffer}"
            results.append({"cmd": "UNKNOWN", "args": { "invalid": "("}, "result": error_result + '\n\nJSON parse error was: ' + parse_fail_reason +
                             tried_to_parse })
 
        return results, full_cmds

    async def execute_command(self, cmd_name, cmd_args, context=None, cmd_id=None):
        """Execute a single command WITHOUT writing the assistant message.

        This is the execution half of handle_cmds, used by the XML/raw-text
        streaming path where the assistant message is persisted once per turn
        (raw text + parsed commands) via chat_log.replace_last_assistant.
        """
        if context.data.get('cancel_current_turn'):
            logger.warning("Turn cancelled, not executing command")
            raise asyncio.CancelledError("Turn cancelled")
        if context.data.get('finished_conversation'):
            logger.warning("Conversation finished, not executing command")
            return None

        command_manager.context = context
        if cmd_name == "reasoning":
            return None
        try:
            if isinstance(cmd_args, list):
                cmd_args = [x for x in cmd_args if x != '']
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
                return await command_manager.execute(cmd_name, *cmd_args)
            elif isinstance(cmd_args, dict):
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
                return await command_manager.execute(cmd_name, **cmd_args)
            else:
                await context.running_command(cmd_name, cmd_args, cmd_id=cmd_id)
                return await command_manager.execute(cmd_name, cmd_args)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            trace = traceback.format_exc()
            print("\033[96mError in execute_command: " + str(e) + "\033[0m")
            print("\033[96m" + trace + "\033[0m")
            logger.error("Error in execute_command", extra={
                "error": str(e), "command": cmd_name, "traceback": trace})
            return {"error": str(e)}

    async def _persist_xml_assistant(self, context, original_buffer, collected):
        """Authoritatively (re)write the current turn's assistant message.

        Stores raw model text (format='xml') plus the parsed command list so the
        UI / cascade deletion / token tooling never have to parse XML.
        """
        content = [{"type": "text", "text": original_buffer, "format": "xml"}]
        try:
            await context.chat_log.replace_last_assistant(content, commands=list(collected))
        except Exception as e:
            logger.error(f"Error persisting xml assistant message: {e}")

    async def parse_xml_cmd_stream(self, stream, context):
        """First-class XML/raw-text command stream parser.

        Text outside tags is spoken (speak command). Tags are commands. No
        XML->JSON->reparse round trip, no JSON buffer surgery, no invalid-format
        error path (the adapter speaks unknown/incomplete tags as literal text).
        """
        results = []
        full_cmds = []
        collected = []           # parsed commands for dual representation
        original_buffer = ""

        emit_chars = 8
        try:
            if context.agent and context.agent.get('xml_emit_partial_on_chars') is not None:
                emit_chars = int(context.agent.get('xml_emit_partial_on_chars'))
        except Exception:
            pass

        ev = XmlEventStream(emit_partial_on_chars=emit_chars)

        # speak segment correlation: partials + the final speak share one cmd_id
        seg_cmd_id = None
        # XML/raw-text mode is primarily for low-latency voice agents. Do not
        # apply the JSON partial throttling knobs here: those exist mainly to
        # protect the UI/event loop during large JSON/code/file outputs. For
        # voice, every speak_partial should reach the TTS partial_command pipe
        # immediately so Kyutai can stream input as soon as text arrives.

        debug_box("Parsing XML command stream")

        async def process_events(events):
            nonlocal seg_cmd_id
            for evt in events:
                kind = evt.get('kind')

                if context.data.get('finished_conversation') or context.data.get('cancel_current_turn'):
                    return True  # signal stop

                if kind == 'speak_partial':
                    text = evt['text']
                    if seg_cmd_id is None:
                        seg_cmd_id = nanoid.generate()
                    await context.partial_command('speak', json.dumps({'text': text}), {'text': text}, cmd_id=seg_cmd_id)

                elif kind == 'speak_final':
                    text = evt['text']
                    if seg_cmd_id is None:
                        seg_cmd_id = nanoid.generate()
                    args = {'text': text}
                    await context.partial_command('speak', json.dumps(args), args, cmd_id=seg_cmd_id)
                    result = await self.execute_command('speak', args, context=context, cmd_id=seg_cmd_id)
                    await context.command_result('speak', result, cmd_id=seg_cmd_id)
                    collected.append({'speak': args})
                    full_cmds.append({"SYSTEM": "", "cmd": "speak", "args": args, "result": result})
                    if result is not None:
                        results.append({"SYSTEM": "", "cmd": "speak", "args": {"omitted": "(see command msg.)"}, "result": result})
                    seg_cmd_id = None
                    await self._persist_xml_assistant(context, original_buffer, collected)

                elif kind == 'cmd':
                    name = evt['name']
                    props = evt['props']
                    cmd_id = nanoid.generate()
                    await context.partial_command(name, json.dumps(props), props, cmd_id=cmd_id)
                    cmd_task = asyncio.create_task(
                        self.execute_command(name, props, context=context, cmd_id=cmd_id)
                    )
                    context.data['active_command_task'] = cmd_task
                    try:
                        result = await cmd_task
                    except asyncio.CancelledError:
                        raise
                    finally:
                        if context.data.get('active_command_task') == cmd_task:
                            del context.data['active_command_task']
                    await context.command_result(name, result, cmd_id=cmd_id)
                    collected.append({name: props})
                    full_cmds.append({"SYSTEM": "", "cmd": name, "args": props, "result": result})

                    if result == "SYSTEM: WARNING - Command interrupted!\n\n":
                        logger.warning("Command was interrupted. Stopping processing.")
                        await context.chat_log.drop_last('assistant')
                        await asyncio.sleep(0.5)
                        return True

                    if result is not None:
                        results.append({"SYSTEM": "", "cmd": name, "args": {"omitted": "(see command msg.)"}, "result": result})
                    await self._persist_xml_assistant(context, original_buffer, collected)
            return False

        stopped = False
        try:
            async for part in stream:
                original_buffer += part
                context.data['_xml_original_buffer'] = original_buffer
                await asyncio.sleep(0)
                stopped = await process_events(ev.feed(part))
                if stopped:
                    try:
                        stream.close()
                    except Exception:
                        pass
                    break
        except asyncio.CancelledError:
            logger.info("XML command stream parsing cancelled")
            raise

        if not stopped:
            await process_events(ev.finish())

        # Final authoritative write (captures any trailing speech).
        await self._persist_xml_assistant(context, original_buffer, collected)

        return results, full_cmds

    async def render_system_msg(self, context):
        t0 = time.time()
        #logger.debug("Docstrings:")
        #logger.debug(command_manager.get_some_docstrings(self.agent["commands"]))
        # Cache json-serialized agent since it doesn't change between renders
        if not hasattr(self, '_agent_json_cache_key'):
            self._agent_json_cache_key = None
        if self._agent_json_cache_key != id(self.agent):
            self._cached_agent_json = json.dumps(self.agent)
            self._agent_json_cache_key = id(self.agent)
        agent_json = self._cached_agent_json
        now = datetime.now()

        formatted_time = now.strftime("~ %Y-%m-%d %I %p %Z%z")

        data = {
            "command_docs": command_manager.get_some_docstrings(self.agent["commands"]),
            "agent": self.agent,
            "persona": self.agent['persona'],
            "formatted_datetime": formatted_time,
            "context_data": self.context.data
        }
   
        for cmd in data['command_docs']:
            if cmd not in command_manager.functions.keys():
                print("Removing " + cmd + " from command_docs")
                del data['command_docs'][cmd]

        xml_mode = xml_streaming_enabled(context)
        if xml_mode:
            # Convert JSON-style command docstrings to compact XML-ish examples
            # so a small voice model is primed to emit tags, not JSON.
            converted = {}
            for _cn, _doc in data['command_docs'].items():
                try:
                    converted[_cn] = convert_docstring_json_examples_to_xml(_doc or '')
                except Exception:
                    converted[_cn] = _doc
            data['command_docs'] = converted

        # Select a clean XML-output system template when XML streaming is on.
        # No plugin defines 'system_xml', so there is no override-precedence
        # ambiguity; the process_system_message pipe below still runs as a hook.
        page = 'system_xml' if xml_mode else 'system'
        #self.system_message = self.sys_template.render(data)
        self.system_message = await render(page, data)
        render_ms = (time.time() - t0) * 1000
        logger.info(f'render_system_msg took {render_ms:.1f}ms')

        # Allow plugins to modify the final system message text (string -> string)
        try:
            tmp = await pipeline_manager.process_system_message({'text': self.system_message, 'data': data}, context=context)
            self.system_message = tmp.get('text', self.system_message)
        except Exception as e:
            logger.error(f"Error in process_system_message pipe: {e}")
 
        additional_instructions = await hook_manager.add_instructions(self.context)

        for instruction in additional_instructions:
            self.system_message += instruction + "\n\n"

        return self.system_message


    async def chat_commands(self, model, context,
                            temperature=0, max_tokens=4000, messages=[]):

        self.context = context
        content = [ { "type": "text", "text": await self.render_system_msg(context) } ]
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

        if 'max_tokens' in context.agent and context.agent['max_tokens'] is not None and context.agent['max_tokens'] != '':
            logger.info(f"Using agent max tokens {max_tokens}")
            max_tokens = context.agent['max_tokens']
        else:
            logger.info(f"Using default max tokens {max_tokens}")

        if model is None:
            if 'service_models' in context.agent and context.agent['service_models'] is not None:
                if context.agent['service_models'].get('stream_chat', None) is None:
                    model = os.environ.get("DEFAULT_LLM_MODEL")
        
        # we need to be able to abort this task if necessary
        stream = await context.stream_chat(model,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        messages=new_messages,
                                        context=context)
        
        try:
            if xml_streaming_enabled(context):
                ret, full_cmds = await self.parse_xml_cmd_stream(stream, context)
            else:
                ret, full_cmds = await self.parse_cmd_stream(stream, context)
        except asyncio.CancelledError:
            logger.info("Command stream parsing cancelled")
            raise  # Propagate cancellation
        
        #logger.debug("System message was:")
        #logger.debug(await self.render_system_msg())

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
