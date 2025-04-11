from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse
from .models import MessageParts
from lib.providers.services import service, service_manager
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages, get_chat_history, run_task
from lib.templates import render
from lib.plugins import list_enabled
import nanoid
from lib.providers.commands import *
import asyncio
from lib.chatcontext import get_context, ChatContext
from typing import List
from lib.providers.services import service, service_manager
from lib.providers.commands import command_manager
from lib.utils.debug import debug_box
from lib.session_files import load_session_data, save_session_data
from pydantic import BaseModel

router = APIRouter()

# Global dictionary to store tasks
tasks = {}

@router.post("/chat/{log_id}/{task_id}/cancel")
async def cancel_chat(request: Request, log_id: str, task_id: str):
    debug_box("cancel_chat")
    print("Trying to cancel task", task_id)
    user = request.state.user.username
    context = await get_context(log_id, user)
    debug_box(str(context))
    context.data['finished_conversation'] = True
    #if task_id in tasks:
    #    task = tasks[task_id]
    #    await asyncio.sleep(0.75)
    #    task.cancel()
    #    del tasks[task_id]
    return {"status": "ok", "message": "Task cancelled successfully"}
    #else:
    #    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/context1/{log_id}")
async def context1(request: Request, log_id: str):
    user = request.state.user.username
    context = await get_context(log_id, user)
    print(context)
    return "ok"

@router.get("/context2/{log_id}")
async def context2(request: Request, log_id: str):
    user = request.state.user.username
    context = await get_context(log_id, user)
    print(context)
    return "ok"


# need to serve persona images from ./personas/local/[persona_name]/avatar.png
@router.get("/chat/personas/{persona_name}/avatar.png")
async def get_persona_avatar(persona_name: str):
    file_path = f"personas/local/{persona_name}/avatar.png"
    if not os.path.exists(file_path):
        return {"error": "File not found"}
        
    with open(file_path, "rb") as f:
        image_bytes = f.read()
    
    return Response(
        content=image_bytes, 
        media_type="image/png",
        headers={
            "Cache-Control": "max-age=3600",
            "Content-Disposition": "inline; filename=avatar.png"
        }
    )


@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    return EventSourceResponse(await subscribe_to_agent_messages(log_id))


@router.post("/chat/{log_id}/send")
async def send_message(request: Request, log_id: str, message_parts: List[MessageParts] ):
    user = request.state.user
    debug_box("send_message")

    context = await get_context(log_id, user.username)
    debug_box(str(context))
    #context = ChatContext(command_manager, service_manager, user=user.user)
    task = asyncio.create_task(send_message_to_agent(log_id, message_parts, context=context, user=user))
    #task = asyncio.create_task(send_message_to_agent(log_id, message_parts, user=user))
     
    task_id = nanoid.generate()
    
    tasks[task_id] = task
    
    return {"status": "ok", "task_id": task_id}

@router.get("/agent/{agent_name}", response_class=HTMLResponse)
async def get_chat_html(request: Request, agent_name: str):
    user = request.state.user
    log_id = nanoid.generate()
    plugins = list_enabled()
    print("Init chat with user", user)
    print(f"Init chat with {agent_name}")
    await init_chat_session(user, agent_name, log_id)

    if hasattr(request.state, "access_token"):
        debug_box("Access token found in request state, saving to session file")
        access_token = request.state.access_token
        await save_session_data(log_id, "access_token", access_token)
        print("..")
        debug_box("Access token saved to session file")
    else:
        debug_box("No access token found in request state")
        
    return RedirectResponse(f"/session/{agent_name}/{log_id}")

@router.get("/history/{agent_name}/{log_id}")
async def chat_history(request: Request, agent_name: str, log_id: str):
    user = request.state.user.username
    history = await get_chat_history(agent_name, log_id, user)
    if history is None or len(history) == 0:
        try:
            print("trying to load from system session")
            history = await get_chat_history(agent_name, log_id, "system")
        except Exception as e:
            print("Error loading from system session:", e)
            history = []
            pass
    return history

@router.get("/session/{agent_name}/{log_id}")
async def chat_history(request: Request, agent_name: str, log_id: str):
    plugins = list_enabled()
    if not hasattr(request.state, "user"):
        return RedirectResponse("/login")

    user = request.state.user
    agent = await service_manager.get_agent_data(agent_name)  
    persona = agent['persona']['name']
    print("persona is:", persona)
    auth_token = None
    try:
        auth_token = await load_session_data(log_id, "access_token")
    except:
        pass
    chat_data = {"log_id": log_id, "agent_name": agent_name, "user": user, "persona": persona }

    if auth_token is not None:
        chat_data["access_token"] = auth_token

    html = await render('chat', chat_data)
    return HTMLResponse(html)

# use starlette staticfiles to mount ./imgs
    app.mount("/published", StaticFiles(directory=str(published_dir)), name="published_indices")

class TaskRequest(BaseModel):
    instructions: str

@router.post("/task/{agent_name}")
async def run_task_route(request: Request, agent_name: str, task_request: TaskRequest = None):
    """
    Run a task for an agent with the given instructions.
    This endpoint allows programmatic interaction with agents without a full chat session.
    
    Parameters:
    - agent_name: The name of the agent to run the task
    - instructions: The instructions/prompt to send to the agent
    
    Returns:
    - JSON with results and log_id for tracking
    """
    
    user = request.state.user.username
    
    instructions = None
    if task_request is not None:
        instructions = task_request.instructions
    
    if not instructions:
        return {"status": "error", "message": "No instructions provided"}
    
    task_result, full_results, log_id = await run_task(instructions=instructions, agent_name=agent_name, user=user)
    print(task_result)
    print(full_results)
    print(log_id)
    return {"status": "ok", "results": task_result, "full_results": full_results, "log_id": log_id}


