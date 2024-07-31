from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
import os
import shutil
import base64
import mimetypes

router = APIRouter()

def get_user_root(username: str):
    if username == 'admin':
        return '/'
    # this should actually be relative to the project root
    # i.e. parent of the parent of the parent  
    proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return f'{proj_root}/data/users/{username}'

def verify_path(user_root: str, path: str):
    if path == '/' or path == '':
        return user_root
    full_path = os.path.normpath(os.path.join(user_root, path))
    if not full_path.startswith(user_root):
        raise HTTPException(status_code=403, detail="Access denied")
    return full_path

def get_directory_structure(path):
    try:
        with os.scandir(path) as entries:
            return {
                'name': os.path.basename(path),
                'type': 'directory',
                'path': path,
                'collapsed': False,
                'children': [
                    get_directory_structure(entry.path) if entry.is_dir() else {
                        'name': entry.name,
                        'type': 'file',
                        'path': entry.path
                    } for entry in entries
                ]
            }

    except PermissionError:
        return {
            'name': os.path.basename(path),
            'type': 'directory',
            'path': path,
            'collapsed': True,
            'children': []
        }

@router.get("/api/file-tree")
async def get_file_tree(request: Request, dir: str = "/"):
    try:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_file_tree')
        user = request.state.user
        print(">>>>>>>>>>>>>>>>>>>>>>>> user: ", user)
        user_root = get_user_root(user['sub'])
        full_path = verify_path(user_root, dir)
        return JSONResponse(get_directory_structure(full_path))
    except Exception as e:
        print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> get_file_tree error: ', e)
        return JSONResponse({"error": str(e)})

@router.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...), path: str = Form(...)):
    user = request.state.user
    user_root = get_user_root(user['sub'])
    print(f'user_root: {user_root}')
    full_path = verify_path(user_root, path)
    file_path = os.path.join(full_path, file.filename)
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to write file")
    
    return JSONResponse({"filename": file.filename, "path": file_path})

@router.delete("/api/delete")
async def delete_file(request: Request, path: str):
    user = request.state.user
    user_root = get_user_root(user['sub'])
    full_path = verify_path(user_root, path)
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            raise HTTPException(status_code=404, detail="File or directory not found")
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to delete file or directory")
    
    return JSONResponse({"status": "success", "path": path})

@router.post("/api/rename")
async def rename_item(request: Request, old_path: str = Form(...), new_name: str = Form(...)):
    user = request.state.user
    user_root = get_user_root(user['sub'])
    full_old_path = verify_path(user_root, old_path)
    new_path = os.path.join(os.path.dirname(full_old_path), new_name)
    
    try:
        os.rename(full_old_path, new_path)
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to rename item")
    
    return JSONResponse({"status": "success", "old_path": old_path, "new_path": new_path})

@router.post("/api/move")
async def move_item(request: Request, old_path: str = Form(...), new_path: str = Form(...)):
    user = request.state.user
    user_root = get_user_root(user['sub'])
    full_old_path = verify_path(user_root, old_path)
    full_new_path = verify_path(user_root, new_path)
    
    try:
        shutil.move(full_old_path, full_new_path)
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to move item")
    
    return JSONResponse({"status": "success", "old_path": old_path, "new_path": new_path})

@router.get("/api/preview")
async def get_file_preview(request: Request, path: str):
    user = request.state.user
    user_root = get_user_root(user['sub'])
    full_path = verify_path(user_root, path)

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        mime_type, _ = mimetypes.guess_type(full_path)
        with open(full_path, 'rb') as file:
            content = file.read()
            if mime_type and mime_type.startswith('text/'):
                preview = content.decode('utf-8')
            else:
                preview = base64.b64encode(content).decode('utf-8')
        return JSONResponse({"preview": preview, "mime_type": mime_type})
    except IOError:
        raise HTTPException(status_code=500, detail="Failed to read file")
