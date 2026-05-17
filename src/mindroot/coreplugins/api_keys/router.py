from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging
from .mod import api_key_manager
from lib.auth.api_key import verify_api_key

router = APIRouter()

logger = logging.getLogger(__name__)

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

def _is_trusted_source(request: Request) -> bool:
    """Check if the request comes from localhost or Docker bridge gateway.

    When mragent on the host connects to a container's mapped port via
    127.0.0.1, Docker NAT rewrites the source IP to the bridge gateway
    (typically 172.17.0.1 or similar). These IPs can only originate from
    processes on the same host, so we trust them for bootstrap operations.
    """
    client_host = request.client.host if request.client else ""
    is_localhost = client_host in ("127.0.0.1", "::1", "localhost")

    if is_localhost:
        return True

    # Docker bridge gateway check: 172.x.0.1 pattern
    is_docker_gateway = False
    if client_host:
        parts = client_host.split(".")
        if len(parts) == 4:
            # Docker default bridge: 172.17.0.0/16, custom bridges: 172.x.0.0/16
            if parts[0] == "172" and parts[2] == "0" and parts[3] == "1":
                is_docker_gateway = True

    # Also check X-Real-IP header in case nginx proxied the request
    # (nginx sets X-Real-IP to the original client IP)
    if not is_docker_gateway:
        real_ip = request.headers.get("X-Real-IP", "")
        if real_ip in ("127.0.0.1", "::1", "localhost"):
            is_docker_gateway = True

    is_trusted = is_localhost or is_docker_gateway
    logger.info(
        f"API key request from {client_host} "
        f"(localhost={is_localhost}, docker_gw={is_docker_gateway}, "
        f"trusted={is_trusted})"
    )
    return is_trusted

@router.post("/api_keys/create")
async def create_api_key(request: Request, key_request: APIKeyCreate):
    """Create a new API key.
    
    Access control:
    - Requests from localhost or Docker bridge gateway are allowed without auth
      (for container bootstrap by mragent on the same host)
    - All other requests require authentication (Bearer token or session user)
    """
    if not _is_trusted_source(request):
        # Require authentication for non-trusted requests
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
async def list_api_keys(request: Request):
    """List API keys. Requires auth unless from localhost."""
    if not _is_trusted_source(request):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_data = await verify_api_key(auth_header[7:])
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid API key")
        elif not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="Authentication required")
    try:
        keys = api_key_manager.list_keys()
        return {"success": True, "data": keys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/api_keys/delete/{api_key}")
async def delete_api_key(api_key: str, request: Request):
    """Delete an API key. Requires auth unless from localhost."""
    if not _is_trusted_source(request):
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_data = await verify_api_key(auth_header[7:])
            if not user_data:
                raise HTTPException(status_code=401, detail="Invalid API key")
        elif not hasattr(request.state, "user"):
            raise HTTPException(status_code=401, detail="Authentication required")
    try:
        success = api_key_manager.delete_key(api_key)
        if success:
            return {"success": True, "message": "API key deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="API key not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
