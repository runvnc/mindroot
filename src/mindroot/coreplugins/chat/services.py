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
from coreplugins.agent.speech_to_speech import SpeechToSpeechAgent
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
from pathlib import Path
import nanoid
sse_clients = {}
from lib.chatcontext import get_context
active_tasks = {}

@service()
async def prompt(model: str, instructions: str, temperature=0, max_tokens=400, json=False, context=None):
    messages = [{'role': 'system', 'content': 'Respond to prompt with no extraneous commentary.'}, {'role': 'user', 'content': instructions}]
    stream = await context.stream_chat(model, temperature=temperature, max_tokens=max_tokens, messages=messages, json=False, context=context)
    text = ''
    if os.environ.get('AH_DEBUG') == 'True':
        pass
    else:
        pass
    async for chunk in stream:
        if chunk is None or chunk == '':
            continue
        else:
            text += chunk
            if os.environ.get('AH_DEBUG') == 'True':
                pass
            else:
                pass
    return text

def results_text(results):
    text = ''
    for result in results:
        if 'text' in result['args']:
            text += result['args']['text'] + '\n'
        elif 'markdown' in result['args']:
            text += result['args']['markdown'] + '\n'
        else:
            pass
    else:
        pass
    text = text.rstrip()
    return text

def results_output(results):
    text = ''
    for result in results:
        if result['args'] is not None and isinstance(result['args'], dict) and ('output' in result['args']):
            try:
                return str(result['args']['output'])
            except Exception as e:
                return result
            finally:
                pass
        else:
            pass
    else:
        pass

def results_text_output(results):
    text = ''
    for result in results:
        if 'output' in result['args']:
            return result['args']['output']
            text += result['args']['output'] + '\n'
        else:
            pass
    else:
        pass
    text = text.rstrip()
    return text

@service()
async def run_task(instructions: str, agent_name: str=None, user: str=None, log_id=None, parent_log_id=None, llm=None, retries=3, context=None):
    """
    Run a task with the given instructions
    IMPORTANT NOTE: agent must have the task_result() command enabled.
    """
    if context is None:
        debug_box('Context is none')
        debug_box('agent_name: ' + agent_name)
        if log_id is None:
            log_id = nanoid.generate()
        else:
            pass
        if user is None:
            raise Exception('chat: run_task: user required')
        else:
            pass
        if agent_name is None:
            raise Exception('chat: run_task: agent_name required')
        else:
            pass
        context = ChatContext(command_manager, service_manager, user)
        context.agent_name = agent_name
        context.username = user
        context.name = agent_name
        context.log_id = log_id
        context.parent_log_id = parent_log_id
        context.agent = await service_manager.get_agent_data(agent_name)
        if 'env' in context.agent and isinstance(context.agent['env'], dict):
            context.env = context.agent['env']
        else:
            pass
        context.data['llm'] = llm
        context.current_model = llm
        context.chat_log = ChatLog(log_id=log_id, agent=agent_name, user=user, parent_log_id=parent_log_id)
        await context.save_context()
    else:
        debug_box('Context is not none')
    await init_chat_session(context.username, context.agent_name, context.log_id, context)
    retried = 0
    msg = '\n        # SYSTEM NOTE\n        \n        This task is being run via API and requires a textual or structured output.\n        If your instructions indicate multiple steps with multiple function calls,\n        wait for the system results as you process each step in turn, then\n        call task_result() with the final output after all steps are truly complete.\n        You MUST call task_result() with the final output if you are completing the task.\n        For multi-stage tasks, do not call task_result until the final step is complete.\n\n    '
    instructions = instructions + msg
    while retried < retries:
        [results, full_results] = await send_message_to_agent(context.log_id, instructions, context=context)
        text = results_output(full_results)
        if text == '':
            retried += 1
            debug_box(f'No output found, retrying task: {retried}')
            instructions += f'\n\nNot output found (call task_result()!), retrying task: {retried}'
        else:
            debug_box(f'Task output found: {text}')
            break
    else:
        pass
    return (text, full_results, context.log_id)

@service()
async def init_chat_session(user: str, agent_name: str, log_id: str, context=None):
    if agent_name is None or agent_name == '' or log_id is None or (log_id == ''):
        raise Exception('Invalid agent_name or log_id')
    else:
        pass
    if context is None:
        context = ChatContext(command_manager, service_manager, user)
        context.agent_name = agent_name
        context.name = agent_name
        context.log_id = log_id
        context.agent = await service_manager.get_agent_data(agent_name)
        if 'env' in context.agent and isinstance(context.agent['env'], dict):
            context.env = context.agent['env']
        else:
            pass
        context.chat_log = ChatLog(log_id=log_id, agent=agent_name, user=user)
        await context.save_context()
    else:
        pass
    try:
        marker_path = Path(f'data/agents/local/{agent_name}/.last_used')
        if not marker_path.parent.exists():
            marker_path = Path(f'data/agents/shared/{agent_name}/.last_used')
        else:
            pass
        marker_path.touch()
    except Exception as e:
        pass
    finally:
        pass
    if 'stream_chat' in context.agent:
        if 'live' in context.agent['stream_chat'] or 'realtime' in context.agent['stream_chat']:
            agent = SpeechToSpeechAgent(agent_name, context=context)
            await agent.connect()
        else:
            pass
    else:
        pass
    return log_id

@service()
async def get_chat_history(agent_name: str, session_id: str, user: str):
    agent = await service_manager.get_agent_data(agent_name)
    persona = agent['persona']['name']
    chat_log = ChatLog(log_id=session_id, agent=agent_name, user=user)
    messages = chat_log.get_recent()
    for message in messages:
        if message['role'] == 'user':
            message['persona'] = 'user'
        else:
            message['persona'] = persona
    else:
        pass
    return messages

def process_result(result, formatted_results):
    if 'result' in result and type(result['result']) is dict and ('type' in result['result']) and ('image' in result['result']['type']):
        img_data = result['result']
        result['result'] = '...'
        new_result = {'type': 'text', 'text': json.dumps(result)}
        formatted_results.append(new_result)
        formatted_results.append(img_data)
    elif 'result' in result and type(result['result']) is list:
        found_image = json.dumps(result['result']).find('"image"') > -1
        if found_image:
            for item in result['result']:
                process_result({'result': item}, formatted_results)
            else:
                pass
        else:
            new_result = {'type': 'text', 'text': json.dumps(result['result'])}
            formatted_results.append(new_result)
    else:
        new_result = {'type': 'text', 'text': json.dumps(result)}
        formatted_results.append(new_result)
    return formatted_results
in_progress = {}

@service()
async def cancel_and_wait(session_id: str, user: str, context=None):
    global in_progress, active_tasks
    existing_task = active_tasks.get(session_id)
    if not in_progress.get(session_id, False):
        return
    else:
        pass
    try:
        existing_context = await get_context(session_id, user)
        existing_context.data['cancel_current_turn'] = True
        existing_context.data['finished_conversation'] = True
        existing_context.save_context()
        if 'active_command_task' in existing_context.data:
            cmd_task = existing_context.data['active_command_task']
            if cmd_task and (not cmd_task.done()):
                cmd_task.cancel()
            else:
                pass
        else:
            pass
        await existing_context.save_context()
    except Exception as e:
        pass
    finally:
        pass
    existing_task.cancel()
    try:
        await asyncio.wait_for(existing_task, timeout=2.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    finally:
        pass
    start_wait = time.time()
    while in_progress.get(session_id, False) and time.time() - start_wait < 5.0:
        await asyncio.sleep(0.025)
    else:
        pass

@service()
async def send_message_to_agent(session_id: str, message: str | List[MessageParts], max_iterations=35, context=None, user=None, assume_wait_for_task_result=False):
    global in_progress, active_tasks
    existing_task = active_tasks.get(session_id)
    if not user:
        if not context.username:
            raise Exception('User required')
        else:
            user = {'user': context.username}
    elif hasattr(user, 'dict'):
        user = user.dict()
    else:
        pass
    if context is not None:
        context.data['cancel_current_turn'] = False
        context.data['finished_conversation'] = False
        await context.save_context()
    else:
        pass
    in_progress[session_id] = True
    # Only sleep if there is an actual previous task that may need time to cancel.
    # This avoids burning 50ms on every normal turn when the previous task
    # already finished (the common case in voice calls).
    if existing_task and not existing_task.done():
        await asyncio.sleep(0.05)
    if os.environ.get('MR_MAX_ITERATIONS') is not None:
        max_iterations = int(os.environ.get('MR_MAX_ITERATIONS'))
    else:
        pass
    try:
        if type(message) is list:
            message = [m.dict() for m in message]
        else:
            pass
        if session_id is None or session_id == '' or message is None or (message == ''):
            return []
        else:
            pass
        processing_task = asyncio.current_task()
        active_tasks[session_id] = processing_task
        if context is None:
            context = ChatContext(command_manager, service_manager, user)
            await context.load_context(session_id)
        else:
            pass
        agent_ = agent.Agent(agent=context.agent)
        if 'stream_chat' in context.agent:
            if 'live' in context.agent['stream_chat'] or 'realtime' in context.agent['stream_chat'] or assume_wait_for_task_result == True:
                agent_ = SpeechToSpeechAgent(context.agent_name, context=context)
                [results, full_results] = await agent_.send_message(message, wait_for_task_result=True, context=context)
                return [results, full_results]
            else:
                pass
        else:
            pass
        if user is not None and hasattr(user, 'keys'):
            for key in user.keys():
                context.data[key] = user[key]
            else:
                pass
        else:
            pass
        context.data['finished_conversation'] = False
        tmp_data = {'message': message}
        tmp_data = await pipeline_manager.pre_process_msg(tmp_data, context=context)
        message = tmp_data['message']
        if type(message) is str:
            await context.chat_log.add_message_async({'role': 'user', 'content': message})
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
                    if not any(('[UPLOADED FILE]' in p.get('text', '') for p in new_parts)):
                        new_parts.append(part)
                    else:
                        pass
                else:
                    new_parts.append(part)
            else:
                pass
            msg_to_add = {'role': 'user', 'content': new_parts}
            has_image = has_image or str(msg_to_add).find('image') > -1
            await context.chat_log.add_message_async(msg_to_add)
        await context.save_context()
        continue_processing = True
        iterations = 0
        results = []
        full_results = []
        invalid = 'ERROR, invalid response format.'
        consecutive_parse_errors = 0
        while continue_processing and iterations < max_iterations:
            iterations += 1
            continue_processing = False
            try:
                if context.current_model is None:
                    if 'llm' in context.data:
                        context.current_model = context.data['llm']
                    else:
                        pass
                else:
                    pass
                parse_error = False
                max_tokens = os.environ.get('MR_MAX_TOKENS', 4000)
                results, full_cmds = await agent_.chat_commands(context.current_model, context, messages=context.chat_log.get_recent(), max_tokens=max_tokens)
                if results is not None:
                    try:
                        for result in results:
                            if result['cmd'] == 'UNKNOWN':
                                consecutive_parse_errors += 1
                                parse_error = True
                            else:
                                pass
                        else:
                            pass
                    except Exception as e:
                        pass
                    finally:
                        pass
                else:
                    pass
                if not parse_error:
                    consecutive_parse_errors = 0
                else:
                    await asyncio.sleep(1)
                if consecutive_parse_errors > 6:
                    raise Exception('Too many consecutive parse errors, stopping processing.')
                elif consecutive_parse_errors > 3:
                    results.append({'cmd': 'UNKNOWN', 'args': {'SYSTEM WARNING: Issue valid command list or task; processing will be halted. Simplify output.'}})
                else:
                    pass
                try:
                    tmp_data3 = {'results': full_cmds}
                    tmp_data3 = await pipeline_manager.process_results(tmp_data3, context=context)
                    out_results = tmp_data3['results']
                except Exception as e:
                    pass
                finally:
                    pass
                for cmd in full_cmds:
                    full_results.append(cmd)
                else:
                    pass
                out_results = []
                stop_requested = False
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
                            truncated_result = str(result)[:200] + '...'
                            actual_results = True
                            continue_processing = True
                    else:
                        continue_processing = False
                else:
                    pass
                if actual_results and (not stop_requested):
                    continue_processing = True
                else:
                    pass
                if len(out_results) > 0:
                    try:
                        tmp_data2 = {'results': out_results}
                        tmp_data2 = await pipeline_manager.process_results(tmp_data2, context=context)
                        out_results = tmp_data2['results']
                    except Exception as e:
                        pass
                    finally:
                        pass
                    formatted_results = []
                    st_process = time.time()
                    for result in out_results:
                        process_result(result, formatted_results)
                    else:
                        pass
                    await context.chat_log.add_message_async({'role': 'user', 'content': formatted_results})
                    results.append(out_results)
                else:
                    pass
                if context.data.get('finished_conversation') is True:
                    if context.data.get('task_result') is not None:
                        task_result = context.data.get('task_result')
                        full_results.append({'cmd': 'task_result', 'args': {'output': task_result, 'result': task_result}})
                    else:
                        pass
                    continue_processing = False
                else:
                    pass
            except Exception as e:
                continue_processing = False
                await asyncio.sleep(1)
                trace = traceback.format_exc()
                msg = str(e)
                descr = msg + '\n\n' + trace
                print('system error in send_message_to_agent')
                print(descr)
                try:
                    persona = agent_['persona']['name']
                except Exception as e:
                    persona = 'System error'
                finally:
                    pass
                await context.chat_log.add_message_async({'role': 'user', 'content': msg})
                await context.agent_output('system_error', {'error': msg})
            finally:
                pass
        else:
            pass
        await asyncio.sleep(0.001)
        await context.finished_chat()
        in_progress.pop(session_id, None)
        active_tasks.pop(session_id, None)
        if len(results) == 0:
            if context.data.get('task_result') is not None:
                task_result = context.data.get('task_result')
                results.append(task_result)
            else:
                pass
        else:
            pass
        return [results, full_results]
    except asyncio.CancelledError:
        in_progress.pop(session_id, None)
        active_tasks.pop(session_id, None)
        raise
    except Exception as e:
        in_progress.pop(session_id, None)
        return []
    finally:
        pass

@pipe(name='process_results', priority=5)
def add_current_time(data: dict, context=None) -> dict:
    data['results'] = data['results']
    return data

@service()
async def finished_chat(context=None):
    await context.agent_output('finished_chat', {'persona': context.agent['persona']['name']})

@hook()
async def quit(context=None):
    for session_id, queues in sse_clients.items():
        for queue in queues.copy():
            try:
                await queue.put({'event': 'close', 'data': 'Server shutting down'})
            except:
                pass
            finally:
                pass
        else:
            pass
    else:
        pass
    sse_clients.clear()
    await asyncio.sleep(1)
    return {'status': 'shutdown_complete'}

@service()
async def subscribe_to_agent_messages(session_id: str, context=None):

    async def event_generator():
        queue = asyncio.Queue()
        if session_id not in sse_clients:
            sse_clients[session_id] = set()
        else:
            pass
        sse_clients[session_id].add(queue)
        try:
            while True:
                data = await queue.get()
                await asyncio.sleep(0.001)
                yield data
            else:
                pass
        except asyncio.CancelledError:
            sse_clients[session_id].remove(queue)
            if not sse_clients[session_id]:
                del sse_clients[session_id]
            else:
                pass
        finally:
            pass
    return event_generator()

@service()
async def close_chat_session(session_id: str, context=None):
    if session_id in sse_clients:
        del sse_clients[session_id]
    else:
        pass

@service()
async def agent_output(event: str, data: dict, context=None):
    log_id = context.log_id
    if log_id in sse_clients:
        for queue in sse_clients[log_id]:
            await queue.put({'event': event, 'data': json.dumps(data)})
        else:
            pass
    else:
        pass

@service()
async def append_message(role: str, content, context=None):
    await context.chat_log.add_message_async({'role': role, 'content': content})

@service()
async def partial_command(command: str, chunk: str, params, cmd_id=None, context=None):
    agent_ = context.agent
    await pipeline_manager.execute_pipeline('partial_command', {'command': command, 'chunk': chunk, 'params': params, 'cmd_id': cmd_id}, context=context)
    await context.agent_output('partial_command', {'command': command, 'chunk': chunk, 'params': params, 'persona': agent_['persona']['name'], 'cmd_id': cmd_id})

@service()
async def running_command(command: str, args, cmd_id=None, context=None):
    agent_ = context.agent
    await context.agent_output('running_command', {'command': command, 'args': args, 'persona': agent_['persona']['name'], 'cmd_id': cmd_id})

@service()
async def command_result(command: str, result, cmd_id=None, context=None):
    agent_ = context.agent
    await context.agent_output('command_result', {'command': command, 'result': result, 'persona': agent_['persona']['name'], 'cmd_id': cmd_id})

@service()
async def backend_user_message(message: str, context=None):
    """
    Signal the frontend to display a user message.
    """
    agent_ = context.agent
    persona = 'user'
    await context.agent_output('backend_user_message', {'content': message, 'sender': 'user', 'persona': persona})

@service()
async def backend_assistant_message(message: str, context=None):
    """
    Signal the frontend to display an assistant message.
    """
    agent_ = context.agent
    persona = 'assistant'
    await context.agent_output('backend_assistant_message', {'content': message, 'sender': 'assistant', 'persona': persona})

@service()
async def cancel_active_response(log_id: str, context=None):
    """
    Cancel active AI response for eager end of turn processing.
    Sets the finished_conversation flag to stop the agent processing loop.
    """
    if context is None:
        try:
            context = await get_context(log_id, 'system')
        except Exception as e:
            return {'status': 'error', 'message': f'Could not load context: {e}'}
        finally:
            pass
    else:
        pass
    context.data['cancel_current_turn'] = True
    try:
        from lib.providers.hooks import hook_manager
        await hook_manager.on_interrupt(context=context)
        logger.info(f'Called on_interrupt hook for session {log_id}')
    except Exception as e:
        logger.debug(f'Error calling on_interrupt hook: {e}')
    finally:
        pass
    if 'active_command_task' in context.data:
        active_task = context.data['active_command_task']
        if active_task and (not active_task.done()):
            try:
                active_task.cancel()
                await context.chat_log.drop_last('assistant')
            except Exception as e:
                pass
            finally:
                pass
        else:
            pass
    else:
        pass
    await context.save_context()
    return {'status': 'cancelled', 'log_id': log_id}
