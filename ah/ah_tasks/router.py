from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .models import TaskDefinition, AdminFileUpload
from .storage import (
    save_task_definition, get_task_definition, list_task_definitions,
    update_task_definition, delete_task_definition
)
import os
import shutil

router = APIRouter()
ADMIN_FILES_DIR = '/files/ah/data/admin_files'

# Mount static files
router.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.jinja2", {"request": request})

# ... (keep all the existing routes)

@router.post("/tasks/{task_name}/admin-files")
async def upload_admin_file(task_name: str, file: UploadFile = File(...), file_description: str = ""):
    task = get_task_definition(task_name)
    
    # Ensure the admin files directory exists
    os.makedirs(ADMIN_FILES_DIR, exist_ok=True)
    
    # Save the uploaded file
    file_path = os.path.join(ADMIN_FILES_DIR, f"{task_name}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Add the file to the task's admin_input_files
    admin_file = AdminFileUpload(
        name=file.filename,
        description=file_description,
        file_path=file_path,
        allowed_extensions=[file.filename.split('.')[-1]]
    )
    task.admin_input_files.append(admin_file)
    
    # Update the task definition
    update_task_definition(task)
    
    return {"message": f"Admin file '{file.filename}' uploaded successfully for task '{task_name}'"}

@router.delete("/tasks/{task_name}/admin-files/{file_name}")
async def delete_admin_file(task_name: str, file_name: str):
    task = get_task_definition(task_name)
    
    # Find and remove the file from the task's admin_input_files
    for admin_file in task.admin_input_files:
        if admin_file.name == file_name:
            task.admin_input_files.remove(admin_file)
            
            # Delete the file from the filesystem
            if os.path.exists(admin_file.file_path):
                os.remove(admin_file.file_path)
            
            # Update the task definition
            update_task_definition(task)
            
            return {"message": f"Admin file '{file_name}' deleted successfully from task '{task_name}'"}
    
    raise HTTPException(status_code=404, detail=f"Admin file '{file_name}' not found for task '{task_name}'")
