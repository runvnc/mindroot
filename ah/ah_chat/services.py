from ..services import service, service_manager
from ..commands import command_manager
from ..chatcontext import ChatContext
from ..chatlog import ChatLog
from ..ah_agent import agent
import colored
import traceback
import asyncio
import json

sse_clients = {}

@service()
async def init_chat_session(agent_name: str, log_id: str):
    context = ChatContext(command_manager, service_manager)
    context.agent_name = agent_name
    context.name = agent_name
    context.log_id = log_id
    context.agent = await service_manager.get_agent_data(agent_name)
    context.chat_log = ChatLog(log_id=log_id, agent=agent_name)
    context.save_context()
    print("initiated_chat_session: ", log_id, agent_name, context.agent_name, context.agent)
    return log_id

@service()
async def send_message_to_agent(session_id: str, message: str, max_iterations=5, context=None):
    print("send_message_to_agent: ", session_id, message, max_iterations)
    context = ChatContext(command_manager, service_manager)
    await context.load_context(session_id)
    print(context) 
    agent_ = agent.Agent(agent=context.agent)
    context.chat_log.add_message({"role": "user", "content": message})
    #results = await agent_.chat_commands(context.current_model, context=context, messages=context.chat_log.get_recent())

    context.save_context()

    continue_processing = True
    iterations = 0
    while continue_processing and iterations < max_iterations:
        iterations += 1
        continue_processing = False
        try:
            results = await agent_.chat_commands(context.current_model, context=context, messages=context.chat_log.get_recent())
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("results from chat commands: ", results)
            out_results = []
            actual_results = False
            asyncio.sleep(0.1)
            for result in results:
                if result['result'] is not None:
                    if result['result'] == 'continue':
                        out_results.append(result)
                        continue_processing = True
                    elif result['result'] == 'stop':
                        continue_processing = False
                    else:
                        out_results.append(result)
                        actual_results = True
                        continue_processing = True
                else:
                    continue_processing = False

            if actual_results:
                continue_processing = True
            
            if len(out_results) > 0:
                print('**********************************************************')
                print("Processing iteration: ", iterations, "adding message")
                context.chat_log.add_message({"role": "user", "content": "[SYSTEM]:\n\n" + json.dumps(out_results, indent=4)})
            else:
                print("Processing iteration: ", iterations, "no message added")
        except Exception as e:
            print("Found an error in agent output: ")
            print(e)
            print(traceback.format_exc())
            continue_processing = False

    await asyncio.sleep(0.1)
    print("Exiting send_message_to_agent: ", session_id, message, max_iterations)
    return results

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
                asyncio.sleep(0.05)
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
    await context.agent_output("running_command", { "command": command, args, "persona": agent_['persona']['name'] })

@service()
async def command_result(command: str, result, context=None):
    agent_ = context.agent
    await context.agent_output("command_result", { "command": command, "result": result, "persona": agent_['persona']['name'] })
