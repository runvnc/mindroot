from ..services import service
from ..chatcontext import ChatContext
from ..chatlog import ChatLog
from ..ah_agent import agent
import asyncio
import json

sse_clients = {}

@service()
async def init_chat_session(agent_name: str, context=None):
    log_id = context.log_id if context else None
    context = ChatContext(command_manager, service_manager)
    context.agent_name = agent_name
    context.log_id = log_id
    context.agent = await service_manager.get_agent_data(agent_name)
    context.chat_log = ChatLog(log_id=log_id, agent=agent_name)
    context.save_context()
    return log_id

@service()
async def send_message_to_agent(session_id: str, message: str, context=None):
    context = await ChatContext.load_context(session_id)
    agent_ = agent.Agent(agent=context.agent)
    context.chat_log.add_message({"role": "user", "content": message})
    results = await agent_.chat_commands(context.current_model, context=context, messages=context.chat_log.get_recent())
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
async def running_command(command: str, context=None):
    agent_ = context.agent
    await context.agent_output("running_command", { "command": command, "persona": agent_['persona']['name'] })

@service()
async def command_result(command: str, result, context=None):
    agent_ = context.agent
    await context.agent_output("command_result", { "command": command, "result": result, "persona": agent_['persona']['name'] })
