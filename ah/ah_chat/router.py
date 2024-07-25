from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from sse_starlette.sse import EventSourceResponse
from .models import Message
from .services import init_chat_session, send_message_to_agent, subscribe_to_agent_messages
from ..ah_templates import render_combined_template
from ..plugins import list_enabled
import nanoid

router = APIRouter()

@router.get("/chat/{log_id}/events")
async def chat_events(log_id: str):
    return EventSourceResponse(subscribe_to_agent_messages(log_id))

@router.put("/chat/{log_id}/{agent_name}")
async def init_chat(log_id: str, agent_name: str):
    await init_chat_session(agent_name, context={"log_id": log_id})
    return {"status": "ok"}

@router.post("/chat/{log_id}/send")
async def send_message(log_id: str, message_data: Message):
    results = await send_message_to_agent(log_id, message_data.message)
    return {"status": "ok", "results": results}

@router.get("/admin", response_class=HTMLResponse)
async def get_admin_html():
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render_combined_template('admin', plugins, {"log_id": log_id})
    return html

@router.get("/{agent_name}", response_class=HTMLResponse)
async def get_chat_html(agent_name: str):
    log_id = nanoid.generate()
    plugins = list_enabled()
    html = await render_combined_template('chat', plugins, {"log_id": log_id, "agent_name": agent_name})
    return html
