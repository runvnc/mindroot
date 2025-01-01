from lib.providers.services import service, service_manager
from lib.providers.commands import command_manager
from lib.pipelines.pipe import pipeline_manager, pipe
from lib.chatcontext import ChatContext
from lib.chatlog import ChatLog
from typing import List
from lib.utils.dataurl import dataurl_to_pil
from .models import MessageParts
from coreplugins.agent import agent
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

sse_clients = {}

@service()
async def init_chat_session(agent_name: str, log_id: str):
    if agent_name is None or agent_name == "" or log_id is None or log_id == "":
        print("Invalid agent_name or log_id")
        print("agent_name: ", agent_name)
        print("log_id: ", log_id)
        raise Exception("Invalid agent_name or log_id")

    context = ChatContext(command_manager, service_manager)
    context.agent_name = agent_name
    context.name = agent_name
    context.log_id = log_id
    context.agent = await service_manager.get_agent_data(agent_name)
    context.chat_log = ChatLog(log_id=log_id, agent=agent_name)
    print("context.agent_name: ", context.agent_name)
    context.save_context()
    print("initiated_chat_session: ", log_id, agent_name, context.agent_name, context.agent)
    return log_id

@service()
async def get_chat_history(session_id: str):
    context = ChatContext(command_manager, service_manager)
    await context.load_context(session_id)
    agent = await service_manager.get_agent_data(context.agent_name)
    
    persona = agent['persona']['name']
    messages = context.chat_log.get_recent()
    for message in messages:
        if message['role'] == 'user':
            message['persona'] = 'user'
        else:
            message['persona'] = persona
    return messages

def process_result(result, formatted_results):
    print("type of result is ", type(result))
    if 'result' in result and type(result['result']) is dict and 'type' in result['result'] and result['result']['type'] == 'image': 
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

@service()
async def send_message_to_agent(session_id: str, message: str | List[MessageParts], max_iterations=35, context=None, user=None):
    try:
        if type(message) is list:
            message = [m.dict() for m in message]

        if session_id is None or session_id == "" or message is None or message == "":
            print("Invalid session_id or message")
            return []

        print("send_message_to_agent: ", session_id, message, max_iterations)
        context = ChatContext(command_manager, service_manager)

        await context.load_context(session_id)
        print(context) 
        agent_ = agent.Agent(agent=context.agent)
        if user is not None:
            for key in user.dict():
                context.data[key] = user.dict()[key]

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
                else:
                    new_parts.append(part)
            msg_to_add= {"role": "user", "content": new_parts }
            has_image = has_image or str(msg_to_add).find("image") > -1
            context.chat_log.add_message(msg_to_add)

        context.save_context()

        continue_processing = True
        iterations = 0
        results = []
        full_results = []

        while continue_processing and iterations < max_iterations:
            iterations += 1
            continue_processing = False
            try:
                if os.environ.get("DEFAULT_LLM_MODEL") is not None:
                    print(2)
                    context.current_model = os.environ.get("DEFAULT_LLM_MODEL")
    
                results, full_cmds = await agent_.chat_commands(context.current_model, context=context, messages=context.chat_log.get_recent())
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
                actual_results = False
                await asyncio.sleep(0.1)
                for result in results:
                    if result['result'] is not None:
                        if result['result'] == 'continue':
                            out_results.append(result)
                            continue_processing = True
                        elif result['result'] == 'stop':
                            continue_processing = False
                        else:
                            out_results.append(result)
                            # only print up to 200 characters
                            truncated_result = str(result)[:200] + '...'
                            termcolor.cprint("Found result: " + truncated_result, "magenta")
                            actual_results = True
                            continue_processing = True
                    else:
                        continue_processing = False

                if actual_results:
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
                    continue_processing = False
            except Exception as e:
                print("Found an error in agent output: ")
                print(e)
                print(traceback.format_exc())
                continue_processing = False

        await asyncio.sleep(0.1)
        print("Exiting send_message_to_agent: ", session_id, message, max_iterations)

        await context.finished_chat()
        return [results, full_results]
    except Exception as e:
        print("Error in send_message_to_agent: ", e)
        print(traceback.format_exc())
        return []

@pipe(name='process_results', priority=5)
def add_current_time(data: dict, context=None) -> dict:
    data['results'] = data['results']
    return data


@service()
async def finished_chat(context=None):
    await context.agent_output("finished_chat", { "persona": context.agent['persona']['name'] })

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
                await asyncio.sleep(0.005)
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

