from fastapi import APIRouter, Request, Response, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
import base64
import json
import mimetypes
from ..commands import command_manager
from ..services import service_manager
from ..chatcontext import ChatContext

router = APIRouter()

async def recent_chats(path):
    try:
        print("recent_chats. dir = ", path)
        files = []
        for file in os.listdir(path):
            files.append(file)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(path, x)), reverse=True)
        print(files)
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
                    "log_id": chat[8:-5],
                    "descr": message["content"][:80],
                    "date": os.path.getmtime(f"{path}/{chat}")
                })
        print(results)
        return results
    except PermissionError:
        raise("Permission denied")
    except Exception as e:
        print("Error in recent_chats")
        print(e)
        raise(str(e))

@router.get("/session_list/{agent}")
async def get_session_list(request: Request, agent: str = "/"):
    try:
        user = request.state.user
        dir = f"data/chat/{agent}"
        #dir = f"data/chat/{user}/{agent}"
        chat = await recent_chats(dir)
        return JSONResponse(chat)
    except Exception as e:
        print("Error in get_session_list")
        print(e)
        return JSONResponse({"error": str(e)})

