from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from .widget_manager import widget_manager
from lib.auth.api_key import verify_api_key
from lib.providers.services import service_manager
from lib.route_decorators import public_route
import nanoid
from .services import init_chat_session
from lib.session_files import save_session_data
import traceback
router = APIRouter()

class WidgetTokenCreate(BaseModel):
    api_key: str
    agent_name: str
    base_url: str
    description: Optional[str] = ''
    styling: Optional[dict] = None

class WidgetTokenResponse(BaseModel):
    token: str
    agent_name: str
    base_url: str
    description: str
    created_at: str
    created_by: str
    styling: dict

@router.post('/widgets/create')
async def create_widget_token(request: Request, widget_request: WidgetTokenCreate):
    """Create a new widget token."""
    try:
        api_key_data = await verify_api_key(widget_request.api_key)
        if not api_key_data:
            raise HTTPException(status_code=400, detail='Invalid API key')
        try:
            agent_data = await service_manager.get_agent_data(widget_request.agent_name)
            if not agent_data:
                raise HTTPException(status_code=400, detail='Agent not found')
        except Exception:
            raise HTTPException(status_code=400, detail='Agent not found')
        user = request.state.user
        token = widget_manager.create_widget_token(api_key=widget_request.api_key, agent_name=widget_request.agent_name, base_url=widget_request.base_url, created_by=user.username, description=widget_request.description, styling=widget_request.styling)
        return {'success': True, 'token': token, 'embed_url': f'{widget_request.base_url}/chat/embed/{token}'}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/widgets/list')
async def list_widget_tokens(request: Request):
    """List widget tokens for the current user."""
    try:
        user = request.state.user
        widgets = widget_manager.list_widget_tokens(created_by=user.username)
        return {'success': True, 'data': widgets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/widgets/delete/{token}')
async def delete_widget_token(request: Request, token: str):
    """Delete a widget token."""
    try:
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail='Widget token not found')
        user = request.state.user
        if widget_config.get('created_by') != user.username:
            raise HTTPException(status_code=403, detail='Not authorized to delete this widget')
        success = widget_manager.delete_widget_token(token)
        if success:
            return {'success': True, 'message': 'Widget token deleted successfully'}
        else:
            raise HTTPException(status_code=500, detail='Failed to delete widget token')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/chat/embed/{token}')
@public_route()
async def get_embed_script(token: str):
    """Generate the secure embed script for a widget token."""
    try:
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail='Widget token not found')
        base_url = widget_config['base_url']
        styling = widget_config.get('styling', {})
        embed_script = f'''\n(function() {{\n    const config = {{\n        baseUrl: "{base_url}",\n        token: "{token}",\n        position: "{styling.get('position', 'bottom-right')}",\n        width: "{styling.get('width', '400px')}",\n        height: "{styling.get('height', '600px')}",\n        theme: "{styling.get('theme', 'dark')}"\n    }};\n    \n    let chatContainer = null;\n    let chatIcon = null;\n    let isLoaded = false;\n    let isMobile = false;\n\n    function detectMobile() {{\n        const userAgent = navigator.userAgent || navigator.vendor || window.opera || "";\n        return /android|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent.toLowerCase());\n    }}\n    \n    function createChatIcon() {{\n        if (chatIcon) return;\n        \n        chatIcon = document.createElement("div");\n        chatIcon.id = "mindroot-chat-icon-" + config.token;\n        chatIcon.innerHTML = "💬";\n        \n        const iconSize = isMobile ? 80 : 60;\n        const fontSize = isMobile ? 28 : 24;\n        const iconStyles = {{\n            position: "fixed",\n            bottom: isMobile ? "30px" : "20px",\n            right: config.position.includes("left") ? "auto" : "20px",\n            left: config.position.includes("left") ? "20px" : "auto",\n            width: iconSize + "px",\n            height: iconSize + "px",\n            background: "#2196F3",\n            borderRadius: "50%",\n            display: "flex",\n            alignItems: "center",\n            justifyContent: "center",\n            cursor: "pointer",\n            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",\n            zIndex: "10000",\n            fontSize: fontSize + "px",\n            color: "white",\n            transition: "all 0.3s ease"\n        }};\n        \n        Object.assign(chatIcon.style, iconStyles);\n        chatIcon.addEventListener("click", toggleChat);\n        document.body.appendChild(chatIcon);\n    }}\n    \n    function createChatContainer() {{\n        if (chatContainer) return;\n        \n        chatContainer = document.createElement("div");\n        chatContainer.id = "mindroot-chat-container-" + config.token;\n        \n        const containerStyles = isMobile ? {{\n            position: "fixed",\n            top: "0px",\n            left: "0",\n            right: "0",\n            bottom: "0",\n            width: "100vw",\n            height: "100vh",\n            background: "white",\n            borderRadius: "0",\n            boxShadow: "none",\n            zIndex: "10001",\n            display: "none",\n            flexDirection: "column",\n            overflow: "hidden"\n        }} : {{\n            position: "fixed",\n            bottom: "90px",\n            right: config.position.includes("left") ? "auto" : "20px",\n            left: config.position.includes("left") ? "20px" : "auto",\n            width: config.width,\n            height: config.height,\n            background: "white",\n            borderRadius: "12px",\n            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",\n            zIndex: "10001",\n            display: "none",\n            overflow: "hidden"\n        }};\n        \n        Object.assign(chatContainer.style, containerStyles);\n        document.body.appendChild(chatContainer);\n    }}\n    \n    function toggleChat() {{\n        if (!chatContainer) createChatContainer();\n        \n        const isVisible = chatContainer.style.display !== "none";\n        \n        if (isVisible) {{\n            chatContainer.style.display = "none";\n            if (isMobile) {{\n                document.body.style.removeProperty("overflow");\n            }}\n        }} else {{\n            if (!isLoaded) {{\n                // Create iframe and load the secure session\n                const iframe = document.createElement("iframe");\n                if (isMobile) {{\n                    iframe.style.cssText = "width: 100%; height: 100%; border: none; position: absolute; top: 0; left: 0; right: 0; bottom: 0;";\n                    // Add viewport meta tag if not present\n                    if (!document.querySelector('meta[name="viewport"]')) {{\n                        const meta = document.createElement('meta');\n                        meta.name = 'viewport';\n                        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no';\n                        document.head.appendChild(meta);\n                    }}\n                }} else {{\n                    iframe.style.cssText = "width: 100%; height: 100%; border: none; border-radius: 12px;";\n                }}\n                iframe.src = config.baseUrl + "/chat/widget/" + config.token + "/session";\n                iframe.setAttribute('allow', 'microphone');\n                chatContainer.appendChild(iframe);\n                isLoaded = true;\n            }}\n            chatContainer.style.display = "block";\n            if (isMobile) {{\n                document.body.style.overflow = "hidden";\n            }}\n        }}\n    }}\n    \n    function init() {{\n        const boot = () => {{\n            isMobile = detectMobile();\n            createChatIcon();\n        }};\n\n        if (document.readyState === "loading") {{\n            document.addEventListener("DOMContentLoaded", boot);\n        }} else {{\n            boot();\n        }}\n    }}\n    \n    init();\n}})();\n'''
        return Response(content=embed_script, media_type='application/javascript', headers={'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/chat/widget/{token}/session')
@public_route()
async def create_widget_session(token: str):
    """Create a secure chat session for a widget token."""
    try:
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail='Widget token not found')
        api_key_data = await verify_api_key(widget_config['api_key'])
        if not api_key_data:
            raise HTTPException(status_code=401, detail='Invalid API key in widget configuration')

        class MockUser:

            def __init__(self, username):
                self.username = username
        user = MockUser(api_key_data['username'])
        session_id = nanoid.generate()
        agent_name = widget_config['agent_name']
        await init_chat_session(user, agent_name, session_id)
        from coreplugins.jwt_auth.middleware import create_access_token
        token_data = create_access_token({'sub': api_key_data['username']})
        await save_session_data(session_id, 'access_token', token_data)
        redirect_url = f'/session/{agent_name}/{session_id}?embed=true'
        return Response(status_code=302, headers={'Location': redirect_url})
    except Exception as e:
        trace = traceback.format_exc()
        raise HTTPException(status_code=500, detail=str(e))