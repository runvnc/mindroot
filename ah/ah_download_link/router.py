from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
import os
import json
from datetime import datetime

router = APIRouter()

@router.get("/download/{download_id}")
async def download_file(download_id: str, request: Request):
    user = 'default'
    link_file = f"data/dl_links/{user}/{download_id}"
    
    if not os.path.exists(link_file):
        raise HTTPException(status_code=404, detail="Download link not found or expired")
    
    with open(link_file, 'r') as f:
        download_info = json.load(f)
    
    file_path = download_info['filename']
    expiry = datetime.strptime(download_info['expiry'], "%Y-%m-%d %H:%M:%S") if download_info['expiry'] != "No expiration" else None
    
    if expiry and datetime.now() > expiry:
        os.remove(link_file)  # Remove expired link
        raise HTTPException(status_code=410, detail="Download link has expired")
    
    if not os.path.exists(file_path):
        os.remove(link_file)  # Remove invalid link
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=os.path.basename(file_path))
