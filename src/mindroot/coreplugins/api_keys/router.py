from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .mod import api_key_manager

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
async def create_api_key(request: APIKeyCreate):
    try:
        key = api_key_manager.create_key(
            username=request.username,
            description=request.description
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
