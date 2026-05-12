from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .mod import api_key_manager
from lib.auth.api_key import verify_api_key

router = APIRouter()

class APIKeyCreate(BaseModel):
    username: str
    description: Optional[str] = ""

class APIKeyResponse(BaseModel):
    key: str
    username: str
    description: str
    created_at: str

class APIKeyList(BaseModel):
    success: bool
    data: List[APIKeyResponse]

@router.post("/api_keys/create")
async def create_api_key(request: Request, key_request: APIKeyCreate):
    """Create a new API key.
    
    Access control:
    - Requests from localhost (127.0.0.1, ::1) are allowed without auth
      (for container bootstrap by mragent)
    - All other requests require authentication (Bearer token or session user)
    """
    # Check if request is from localhost
    client_host = request.client.host if request.client else ""
    is_localhost = client_host in ("127.0.0.1", "::1", "localhost")
    
    if not is_localhost:
        # Require authentication for non-localhost requests
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_data = await verify_api_key(auth_header[7:])
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid API key")
        elif not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="Authentication required")
    try:
        key = api_key_manager.create_key(
            username=key_request.username,
            description=key_request.description
        )
        return {"success": True, "data": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api_keys/list", response_model=APIKeyList)
async def list_api_keys():
    try:
        keys = api_key_manager.list_keys()
        return {"success": True, "data": keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api_keys/delete/{api_key}")
async def delete_api_key(api_key: str):
    try:
        success = api_key_manager.delete_key(api_key)
        if success:
            return {"success": True, "message": "API key deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
