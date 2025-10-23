from lib.providers.services import service, service_manager
from lib.providers.commands import command_manager, command
from lib.providers.hooks import hook
from lib.pipelines.pipe import pipeline_manager, pipe
from lib.chatcontext import ChatContext
from lib.chatlog import ChatLog
from typing import List
from lib.utils.dataurl import dataurl_to_pil
from .models import MessageParts
from coreplugins.agent import agent
from lib.utils.debug import debug_box
import os
import sys
import colored
import time
import traceback
import asyncio
import json
import termcolor
from PIL import Image
from io import BytesIO
import base64
import nanoid
sse_clients = {}
from lib.chatcontext import get_context

# Track active processing tasks per session
active_tasks = {}

@service()
async def prompt(model: str, instructions: str, temperature=0, max_tokens=400, json=False, context=None):
    messages = [
        { "role": "system",
          "content": "Respond to prompt with no extraneous commentary."
        },
        { "role": "user",
          "content": instructions
        }]
    
    stream = await context.stream_chat(model, temperature=temperature,
                                       max_tokens=max_tokens,
                                       messages=messages,
                                       json=False,
                                       context=context)
    text = ""
    if os.environ.get("AH_DEBUG") == "True":
        print("Prompting, instructions ", instructions)
    async for chunk in stream:
        #print("Chunk received: ", chunk)
        if chunk is None or chunk == "":
            continue
        else:
            text += chunk
            if os.environ.get("AH_DEBUG") == "True":
                print(chunk, end='', flush=True)

    return text


def results_text(results):
    text = ""
    for result in results:
        if 'text' in result['args']:
            text += result['args']['text'] + "\n"
        elif 'markdown' in result['args']:
            text += result['args']['markdown'] + "\n"
    text = text.rstrip()
    return text

def results_output(results):
    text = ""
    for result in results:
        if 'output' in result['args']:
            return str(result['args']['output'])

def results_text_output(results):
    text = ""
    for result in results:
        if 'output' in result['args']:
            return result['args']['output']
            text += result['args']['output'] + "\n"
    text = text.rstrip()
    return text

    
@service()
async def run_task(instructions: str, agent_name:str = None, user:str = None, log_id=None, 
                   parent_log_id=None, llm=None, retries=3, context=None):
    """
    Run a task with the given instructions
    IMPORTANT NOTE: agent must have the task_result() command enabled.
    """

    if context is None:
        debug_box("Context is none")
        debug_box("agent_name: " + agent_name)
        if log_id is None:
            log_id = nanoid.generate()
        if user is None:
            raise Exception("chat: run_task: user required")
        if agent_name is None:
            raise Exception("chat: run_task: agent_name required")
        context = ChatContext(command_manager, service_manager, user)
        context.agent_name = agent_name
        context.username = user
        context.name = agent_name
        context.log_id = log_id
        context.parent_log_id = parent_log_id
        context.agent = await service_manager.get_agent_data(agent_name)
        context.data['llm'] = llm
        context.current_model = llm
        context.chat_log = ChatLog(log_id=log_id, agent=agent_name, user=user, parent_log_id=parent_log_id)
        await context.save_context()
    else:
        debug_box("Context is not none")
        print(context)
        
     
    print("run_task: ", instructions, "log_id: ", context.log_id)
    
    await init_chat_session(context.username, context.agent_name, context.log_id, context)

    retried = 0

    msg = """
        # SYSTEM NOTE
        
        This task is being run via API and requires a textual or structured output.
        If your instructions indicate multiple steps with multiple function calls,
        wait for the system results as you process each step in turn, then
        call task_result() with the final output after all steps are truly complete.
        You MUST call task_result() with the final output if you are completing the task.
        For multi-stage tasks, do not call task_result until the final step is complete.

    """

    instructions = instructions + msg

    while retried < retries:
        [results, full_results] = await send_message_to_agent(context.log_id, instructions, context=context)
        print('#####################################################33')
        print("Full results: ", full_results)
        print("Results: ", results)
        text = results_output(full_results)
        if text == "":
            retried += 1
            debug_box(f"No output found, retrying task: {retried}")
            instructions += f"\n\nNot output found (call task_result()!), retrying task: {retried}"
        else:
            debug_box(f"Task output found: {text}")
            break

    return (text, full_results, context.log_id)


@service()
async def init_chat_session(user:str, agent_name: str, log_id: str, context=None):
    if agent_name is None or agent_name == "" or log_id is None or log_id == "":
        print("Invalid agent_name or log_id")
        print("agent_name: ", agent_name)
        print("log_id: ", log_id)
        raise Exception("Invalid agent_name or log_id")

    if context is None:
        context = ChatContext(command_manager, service_manager, user)
        context.agent_name = agent_name
        context.name = agent_name
        context.log_id = log_id
        context.agent = await service_manager.get_agent_data(agent_name)
        context.chat_log = ChatLog(log_id=log_id, agent=agent_name, user=user)
        print("context.agent_name: ", context.agent_name)
        await context.save_context()
    print("initiated_chat_session: ", log_id, agent_name, context.agent_name, context.agent)
    return log_id

@service()
async def get_chat_history(agent_name: str, session_id: str, user:str):
    print("-----------------")
    print("get_chat_history: ", agent_name, session_id)
    #context = ChatContext(command_manager, service_manager)
    #await context.load_context(session_id)
    agent = await service_manager.get_agent_data(agent_name)
    
    persona = agent['persona']['name']
    chat_log = ChatLog(log_id=session_id, agent=agent_name, user=user)
    print("Got chat chat log")
    messages = chat_log.get_recent()
    print("messages length: ", len(messages))
    for message in messages:
        if message['role'] == 'user':
            message['persona'] = 'user'
        else:
            message['persona'] = persona
    return messages

def process_result(result, formatted_results):
    print("type of result is ", type(result))
    if 'result' in result and type(result['result']) is dict and 'type' in result['result'] and 'image' in result['result']['type']: 
        print("A")
        img_data = result['result']
        result['result'] = '...'
        new_result = { "type": "text", "text": json.dumps(result) } 
        formatted_results.append(new_result)
        formatted_results.append(img_data)
    elif 'result' in result and type(result['result']) is list:
        print("B")
        found_image = json.dumps(result['result']).find('"image"') > -1
        if found_image:
            print("Found image")
            for item in result['result']:
                process_result({ "result": item}, formatted_results)
        else:
            new_result = { "type": "text", "text": json.dumps(result['result']) }
            formatted_results.append(new_result)
    else:
        print("C")
        new_result = { "type": "text", "text": json.dumps(result) }
        formatted_results.append(new_result)
    
    print("length of results is ", len(formatted_results))
    #with open("output/processed_results.json", "w") as f: 
    #    f.write(json.dumps(formatted_results) + "\n")

    return formatted_results

# Deprecated - use active_tasks instead
in_progress = {}


# seems like sometimes it's too late to cancel
# so I tried just aborting
# but then the other one got cancelled by the interruption
# and since this was cancelled, we never responded
#
# but if we try to continue, we end up with both running

@service()
async def send_message_to_agent(session_id: str, message: str | List[MessageParts], max_iterations=35, context=None, user=None):
    global in_progress, active_tasks
    
    # Check if there's an active task for this session
    existing_task = active_tasks.get(session_id)

    if not user:
        # check context
        if not context.username:
            raise Exception("User required")
        else:
            user = {"user": context.username }
    else:
        if hasattr(user, "dict"):
            user = user.dict()

    # If there's an existing task, cancel it and wait for it to finish
    if existing_task and not existing_task.done():
        print(f"SEND_MESSAGE: Cancelling existing task for session {session_id}")
        
        # Load the context to set cancellation flags
        try:
            existing_context = await get_context(session_id, user)
            existing_context.data['cancel_current_turn'] = True
            
            # Cancel any active command task
            if 'active_command_task' in existing_context.data:
                cmd_task = existing_context.data['active_command_task']
                if cmd_task and not cmd_task.done():
                    cmd_task.cancel()
            
            await existing_context.save_context()
        except Exception as e:
            print(f"Error setting cancellation flags: {e}")
        
        # Cancel the main task
        existing_task.cancel()
        
        # Wait for it to actually finish (with timeout)
        try:
            await asyncio.wait_for(existing_task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass  # Expected
        
        print(f"Previous task cancelled for session {session_id}")
    
    in_progress[session_id] = True

    print('b')
    if os.environ.get("MR_MAX_ITERATIONS") is not None:
        max_iterations = int(os.environ.get("MR_MAX_ITERATIONS"))
    try:
        if type(message) is list:
            message = [m.dict() for m in message]

        if session_id is None or session_id == "" or message is None or message == "":
            print("Invalid session_id or message")
            return []

        # Create the main processing task and store it
        processing_task = asyncio.current_task()
        active_tasks[session_id] = processing_task

        print("send_message_to_agent: ", session_id, message, max_iterations)
        if context is None:
            context = ChatContext(command_manager, service_manager, user)
            await context.load_context(session_id)

        agent_ = agent.Agent(agent=context.agent)
        if user is not None and hasattr(user, "keys"):
            for key in user.keys():
                context.data[key] = user[key]

        context.data['finished_conversation'] = False

        tmp_data = { "message": message }
        tmp_data = await pipeline_manager.pre_process_msg(tmp_data, context=context)
        message = tmp_data['message']

        termcolor.cprint("Final message: " + str(message), "yellow")
        if type(message) is str:
            #context.chat_log.add_message({"role": "user", "content": [{"type": "text", "text": message}]})
            context.chat_log.add_message({"role": "user", "content": message })
        else:
            new_parts = []
            has_image = False
            for part in message:
                if part['type'] == 'image':
                    has_image = True
                    img = dataurl_to_pil(part['data'])
                    img_msg = await context.format_image_message(img)
                    new_parts.append(img_msg)
                elif part['type'] == 'text' and '[UPLOADED FILE]' in part['text']:
                    # Ensure we don't duplicate file entries
                    if not any('[UPLOADED FILE]' in p.get('text', '') for p in new_parts):
                        new_parts.append(part)
                else:
                    new_parts.append(part)
            msg_to_add= {"role": "user", "content": new_parts }
            has_image = has_image or str(msg_to_add).find("image") > -1
            context.chat_log.add_message(msg_to_add)

        await context.save_context()

        continue_processing = True
        iterations = 0
        results = []
        full_results = []

        invalid = "ERROR, invalid response format."
        
        consecutive_parse_errors = 0

        while continue_processing and iterations < max_iterations:
            iterations += 1
            continue_processing = False
            try:
                if context.current_model is None:
                    if 'llm' in context.data:
                        context.current_model = context.data['llm']
    
                parse_error = False
                max_tokens = os.environ.get("MR_MAX_TOKENS", 4000)
                results, full_cmds = await agent_.chat_commands(context.current_model, context, messages=context.chat_log.get_recent(), max_tokens=max_tokens)
                if results is not None:
                    try:
                        for result in results:
                            if result['cmd'] == 'UNKNOWN':
                                consecutive_parse_errors += 1
                                parse_error = True
                    except Exception as e:
                        pass

                if not parse_error:
                    consecutive_parse_errors = 0
                else:
                    await asyncio.sleep(1)

                if consecutive_parse_errors > 6:
                    raise Exception("Too many consecutive parse errors, stopping processing.")

                elif consecutive_parse_errors > 3: 
                    results.append({"cmd": "UNKNOWN", "args": { "SYSTEM WARNING: Issue valid command list or task; processing will be halted. Simplify output."}})

                try:
                    tmp_data3 = { "results": full_cmds }
                    tmp_data3 = await pipeline_manager.process_results(tmp_data3, context=context)
                    out_results = tmp_data3['results']
                except Exception as e:
                    print("Error processing results: ", e)
                    print(traceback.format_exc())

                for cmd in full_cmds:
                    full_results.append(cmd)
                out_results = []
                stop_requested= False
                actual_results = False
                await asyncio.sleep(0.001)
                for result in results:
                    if 'result' in result and result['result'] is not None:
                        if result['result'] == 'continue':
                            out_results.append(result)
                            continue_processing = True
                        elif result['result'] == 'stop':
                            continue_processing = False
                            stop_requested = True
                        else:
                            out_results.append(result)
                            # only print up to 200 characters
                            truncated_result = str(result)[:200] + '...'
                            termcolor.cprint("Found result: " + truncated_result, "magenta")
                            actual_results = True
                            continue_processing = True
                    else:
                        continue_processing = False

                if actual_results and not stop_requested:
                    continue_processing = True
                
                if len(out_results) > 0:
                    try:
                        tmp_data2 = { "results": out_results }
                        tmp_data2 = await pipeline_manager.process_results(tmp_data2, context=context)
                        out_results = tmp_data2['results']
                    except Exception as e:
                        print("Error processing results: ", e)
                        print(traceback.format_exc())

                    formatted_results = []
                    st_process = time.time()
                    for result in out_results:
                        process_result(result, formatted_results)
                    print("Time to process results: ", time.time() - st_process)
                    
                    context.chat_log.add_message({"role": "user", "content": formatted_results})
                    results.append(out_results) 
                else:
                    print("Processing iteration: ", iterations, "no message added")
                if context.data.get('finished_conversation') is True:
                    termcolor.cprint("Finished conversation, exiting send_message_to_agent", "red")
                    if context.data.get('task_result') is not None:
                        task_result = context.data.get('task_result')
                        full_results.append({ "cmd": "task_result", "args": { "result": task_result } })
                    continue_processing = False
            except Exception as e:
                continue_processing = False
                await asyncio.sleep(1)
                trace = traceback.format_exc()
                msg = str(e)
                descr = msg + "\n\n" + trace
                print(descr)

                print('------')
                print(msg)
                try:
                    persona = agent_['persona']['name']
                except Exception as e:
                    persona = "System error"
                context.chat_log.add_message({"role": "user", "content": msg })
                await context.agent_output("system_error", { "error": msg })
                

        await asyncio.sleep(0.001)
        print("Exiting send_message_to_agent: ", session_id, message, max_iterations)

        await context.finished_chat()
        in_progress.pop(session_id, None)
        active_tasks.pop(session_id, None)
        if len(results) == 0:
            if context.data.get('task_result') is not None:
                task_result = context.data.get('task_result')
                results.append(task_result)
        return [results, full_results]
    except asyncio.CancelledError:
        print(f"Task cancelled for session {session_id}")
        in_progress.pop(session_id, None)
        active_tasks.pop(session_id, None)
        raise  # Re-raise to properly handle cancellation
    except Exception as e:
        print("Error in send_message_to_agent: ", e)
        print(traceback.format_exc())
        in_progress.pop(session_id, None)
        return []

@pipe(name='process_results', priority=5)
def add_current_time(data: dict, context=None) -> dict:
    data['results'] = data['results']
    return data


@service()
async def finished_chat(context=None):
    await context.agent_output("finished_chat", { "persona": context.agent['persona']['name'] })

@hook()
async def quit(context=None):
    print("Chat service is quitting..")
    # Close all existing SSE connections
    for session_id, queues in sse_clients.items():
        for queue in queues.copy():  # Use copy to avoid modification during iteration
            try:
                await queue.put({'event': 'close', 'data': 'Server shutting down'})
            except:
                pass
    
    # Clear the global sse_clients
    sse_clients.clear()
    
    # Give clients a moment to receive the close message
    await asyncio.sleep(1)
    print("Chat service finished.") 
    return {"status": "shutdown_complete"}

@service()
async def subscribe_to_agent_messages(session_id: str, context=None):
    async def event_generator():
        queue = asyncio.Queue()
        if session_id not in sse_clients:
            sse_clients[session_id] = set()
        sse_clients[session_id].add(queue)
        try:
            while True:
                data = await queue.get()
                await asyncio.sleep(0.001)
                print('.', end='', flush=True)
                yield data
        except asyncio.CancelledError:
            sse_clients[session_id].remove(queue)
            if not sse_clients[session_id]:
                del sse_clients[session_id]
    return event_generator()

@service()
async def close_chat_session(session_id: str, context=None):
    if session_id in sse_clients:
        del sse_clients[session_id]
    # Any additional cleanup needed

@service()
async def agent_output(event: str, data: dict, context=None):
    log_id = context.log_id
    if log_id in sse_clients:
        for queue in sse_clients[log_id]:
            await queue.put({"event": event, "data": json.dumps(data)})

@service()
async def append_message(role: str, content, context=None):
    await context.chat_log.add_message({"role": role, "content": content})

@service()
async def partial_command(command: str, chunk: str, params, context=None):
    agent_ = context.agent
    await context.agent_output("partial_command", { "command": command, "chunk": chunk, "params": params,
                                                    "persona": agent_['persona']['name'] })

@service()
async def running_command(command: str, args, context=None):
    agent_ = context.agent
    await context.agent_output("running_command", { "command": command, "args": args, "persona": agent_['persona']['name'] })

@service()
async def command_result(command: str, result, context=None):
    agent_ = context.agent
    await context.agent_output("command_result", { "command": command, "result": result, "persona": agent_['persona']['name'] })

@service()
async def backend_user_message(message: str, context=None):
    """
    Signal the frontend to display a user message.
    """
    agent_ = context.agent
    persona = 'user'
    await context.agent_output("backend_user_message", { 
        "content": message, 
        "sender": "user",
        "persona": persona
    })

@service()
async def cancel_active_response(log_id: str, context=None):
    """
    Cancel active AI response for eager end of turn processing.
    Sets the finished_conversation flag to stop the agent processing loop.
    """
    if context is None:
        # Get context from log_id - we need the username, but for SIP calls it might be 'system'
        # Try to load context, fallback to system user if needed
        try:
            context = await get_context(log_id, 'system')
        except Exception as e:
            print(f"Error getting context for cancellation: {e}")
            return {"status": "error", "message": f"Could not load context: {e}"}
    
    # Set flag to stop current processing loop iteration
    # But don't permanently mark conversation as finished - just this turn
    context.data['cancel_current_turn'] = True
    
    # DEBUG TRACE
    print("\033[91;107m[DEBUG TRACE 5/6] Core cancel_active_response service executed.\033[0m")
    
    # Cancel any active TTS streams (ElevenLabs)
    try:
        # Import here to avoid circular dependency
        from mr_eleven_stream.mod import _active_tts_streams
        for stream_id, stop_event in list(_active_tts_streams.items()):
            stop_event.set()
            logger.info(f"Cancelled TTS stream {stream_id}")
            print("\033[91;107m[DEBUG TRACE 5.5/6] Cancelled active TTS stream.\033[0m")
    except ImportError:
        logger.debug("ElevenLabs TTS plugin not available for cancellation")
    
    # Also, cancel any active command task (like speak())
    if 'active_command_task' in context.data:
        active_task = context.data['active_command_task']
        if active_task and not active_task.done():
            try:
                active_task.cancel()
                # DEBUG TRACE
                print("\033[91;107m[DEBUG TRACE 6/6] Active command task found and cancelled.\033[0m")
                print(f"Cancelled active command task for session {log_id}")
            except Exception as e:
                print(f"Error cancelling active command task: {e}")
    
    await context.save_context()
    
    print(f"Cancelled active response for session {log_id}")
    return {"status": "cancelled", "log_id": log_id}

