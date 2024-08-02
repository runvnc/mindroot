from fastapi import APIRouter, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
import base64
import mimetypes
from ..commands import command_manager
from ..services import service_manager
from ..chatcontext import ChatContext

router = APIRouter()

def recent_chats(path):
    try:
        files = []
        for file in os.listdir(path):
            files.append(file)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
        chats = files[:30]
        results = []
        for chat in chats:
            with open(f"{path}/{chat}", "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                continue
            message = data["messages"][0]
            results.append({
                "content": message["content"][:30],
                "timestamp": os.path.getmtime(f"{path}/{chat}")
            })
        return results
    except PermissionError:
        throw("Permission denied")

@router.get("/history/{agent}")
async def get_file_tree(request: Request, dir: str = "/"):
    try:
        user = request.state.user
        dir = f"data/chat/{agent}"
        #dir = f"data/chat/{user}/{agent}"
        return JSONResponse(await recent_chats(dir))
    except Exception as e:
        return JSONResponse({"error": str(e)})

