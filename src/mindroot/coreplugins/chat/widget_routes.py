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
    description: Optional[str] = ""
    styling: Optional[dict] = None

class WidgetTokenResponse(BaseModel):
    token: str
    agent_name: str
    base_url: str
    description: str
    created_at: str
    created_by: str
    styling: dict

@router.post("/widgets/create")
async def create_widget_token(request: Request, widget_request: WidgetTokenCreate):
    """Create a new widget token."""
    try:
        # Verify the API key is valid
        api_key_data = await verify_api_key(widget_request.api_key)
        if not api_key_data:
            raise HTTPException(status_code=400, detail="Invalid API key")
        
        # Verify the agent exists
        try:
            agent_data = await service_manager.get_agent_data(widget_request.agent_name)
            if not agent_data:
                raise HTTPException(status_code=400, detail="Agent not found")
        except Exception:
            raise HTTPException(status_code=400, detail="Agent not found")
        
        # Get the current user
        user = request.state.user
        
        # Create the widget token
        token = widget_manager.create_widget_token(
            api_key=widget_request.api_key,
            agent_name=widget_request.agent_name,
            base_url=widget_request.base_url,
            created_by=user.username,
            description=widget_request.description,
            styling=widget_request.styling
        )
        
        return {
            "success": True,
            "token": token,
            "embed_url": f"{widget_request.base_url}/chat/embed/{token}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/widgets/list")
async def list_widget_tokens(request: Request):
    """List widget tokens for the current user."""
    try:
        user = request.state.user
        widgets = widget_manager.list_widget_tokens(created_by=user.username)
        return {"success": True, "data": widgets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/widgets/delete/{token}")
async def delete_widget_token(request: Request, token: str):
    """Delete a widget token."""
    try:
        # Verify the widget exists and belongs to the user
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail="Widget token not found")
        
        user = request.state.user
        if widget_config.get("created_by") != user.username:
            raise HTTPException(status_code=403, detail="Not authorized to delete this widget")
        
        success = widget_manager.delete_widget_token(token)
        if success:
            return {"success": True, "message": "Widget token deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete widget token")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/embed/{token}")
@public_route()
async def get_embed_script(token: str):
    """Generate the secure embed script for a widget token."""
    try:
        # Validate the widget token
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail="Widget token not found")
        
        # Generate the embed JavaScript
        base_url = widget_config["base_url"]
        styling = widget_config.get("styling", {})
        
        # Create the embed script that doesn't expose the API key
        embed_script = f'''
(function() {{
    const config = {{
        baseUrl: "{base_url}",
        token: "{token}",
        position: "{styling.get('position', 'bottom-right')}",
        width: "{styling.get('width', '400px')}",
        height: "{styling.get('height', '600px')}",
        theme: "{styling.get('theme', 'dark')}"
    }};
    
    let chatContainer = null;
    let chatIcon = null;
    let isLoaded = false;
    
    function createChatIcon() {{
        if (chatIcon) return;
        
        chatIcon = document.createElement("div");
        chatIcon.id = "mindroot-chat-icon-" + config.token;
        chatIcon.innerHTML = "💬";
        
        const iconStyles = {{
            position: "fixed",
            bottom: "20px",
            right: config.position.includes("left") ? "auto" : "20px",
            left: config.position.includes("left") ? "20px" : "auto",
            width: "60px",
            height: "60px",
            background: "#2196F3",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
            zIndex: "10000",
            fontSize: "24px",
            color: "white",
            transition: "all 0.3s ease"
        }};
        
        Object.assign(chatIcon.style, iconStyles);
        chatIcon.addEventListener("click", toggleChat);
        document.body.appendChild(chatIcon);
    }}
    
    function createChatContainer() {{
        if (chatContainer) return;
        
        chatContainer = document.createElement("div");
        chatContainer.id = "mindroot-chat-container-" + config.token;
        
        const containerStyles = {{
            position: "fixed",
            bottom: "90px",
            right: config.position.includes("left") ? "auto" : "20px",
            left: config.position.includes("left") ? "20px" : "auto",
            width: config.width,
            height: config.height,
            background: "white",
            borderRadius: "12px",
            boxShadow: "0 8px 32px rgba(0, 0, 0, 0.3)",
            zIndex: "10001",
            display: "none",
            overflow: "hidden"
        }};
        
        Object.assign(chatContainer.style, containerStyles);
        document.body.appendChild(chatContainer);
    }}
    
    function toggleChat() {{
        if (!chatContainer) createChatContainer();
        
        const isVisible = chatContainer.style.display !== "none";
        
        if (isVisible) {{
            chatContainer.style.display = "none";
        }} else {{
            if (!isLoaded) {{
                // Create iframe and load the secure session
                const iframe = document.createElement("iframe");
                iframe.style.cssText = "width: 100%; height: 100%; border: none; border-radius: 12px;";
                iframe.src = config.baseUrl + "/chat/widget/" + config.token + "/session";
                chatContainer.appendChild(iframe);
                isLoaded = true;
            }}
            chatContainer.style.display = "block";
        }}
    }}
    
    function init() {{
        if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", function() {{
                createChatIcon();
            }});
        }} else {{
            createChatIcon();
        }}
    }}
    
    init();
}})();
'''
        
        return Response(
            content=embed_script,
            media_type="application/javascript",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/widget/{token}/session")
@public_route()
async def create_widget_session(token: str):
    """Create a secure chat session for a widget token."""
    try:
        # Validate the widget token
        widget_config = widget_manager.get_widget_config(token)
        if not widget_config:
            raise HTTPException(status_code=404, detail="Widget token not found")
        
        # Verify the API key from the widget config
        api_key_data = await verify_api_key(widget_config["api_key"])
        if not api_key_data:
            raise HTTPException(status_code=401, detail="Invalid API key in widget configuration")
        
        # Create mock user and generate session ID
        class MockUser:
            def __init__(self, username):
                self.username = username
        user = MockUser(api_key_data['username'])
        session_id = nanoid.generate()
        agent_name = widget_config["agent_name"]
        
        # Initialize the chat session (this was missing!)
        await init_chat_session(user, agent_name, session_id)
        
        # Create and save access token for authentication
        from coreplugins.jwt_auth.middleware import create_access_token
        token_data = create_access_token({"sub": api_key_data['username']})
        await save_session_data(session_id, "access_token", token_data)
        
        # Now redirect to the session WITHOUT exposing the API key
        redirect_url = f"/session/{agent_name}/{session_id}?embed=true"
        
        return Response(
            status_code=302,
            headers={"Location": redirect_url}
        )
    
    except Exception as e:
        trace = traceback.format_exc()
        print(e, trace)
        raise HTTPException(status_code=500, detail=str(e))
        
