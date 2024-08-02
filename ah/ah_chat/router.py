from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse
from .models import Message
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages, get_chat_history
from ..ah_templates import render_combined_template
from ..plugins import list_enabled
import nanoid
from  .commands import *

router = APIRouter()

@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    return EventSourceResponse(await subscribe_to_agent_messages(log_id))

@router.post("/chat/{log_id}/send")
async def send_message(request:Request, log_id: str, message_data: Message):
    user = request.state.user
    print(f"send_message   log_id: {log_id}   message: {message_data.message}")
    results = await send_message_to_agent(log_id, message_data.message, user=user)
    return {"status": "ok", "results": results}

@router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render_combined_template('admin', plugins, {"log_id": log_id})
    return html

@router.get("/agent/{agent_name}", response_class=HTMLResponse)
async def get_chat_html(agent_name: str):
    log_id = nanoid.generate()
    plugins = list_enabled()
    await init_chat_session(agent_name, log_id)
    return RedirectResponse(f"/session/{agent_name}/{log_id}")

@router.get("/history/{log_id}")
async def chat_history(log_id: str):
    history = await get_chat_history(log_id)
    return history


@router.get("/session/{agent_name}/{log_id}")
async def chat_history(agent_name: str, log_id: str):
    plugins = list_enabled()
    user = request.state.user
    html = await render_combined_template('chat', plugins, {"log_id": log_id, "agent_name": agent_name, "user": user})
    return HTMLResponse(html)
    return html

