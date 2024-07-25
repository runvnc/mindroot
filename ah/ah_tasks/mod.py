from ..commands import command
from .models import TaskDefinition, TaskInstance, TaskStatus, AdminFileUpload
from .storage import (
    save_task_definition, get_task_definition, list_task_definitions,
    update_task_definition, delete_task_definition,
    save_task_instance, get_task_instance, list_task_instances,
    update_task_instance, delete_task_instance
)
from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import os
import shutil
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()
ADMIN_FILES_DIR = '/files/ah/data/admin_files'

# Mount static files
router.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.jinja2", {"request": request})

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

@command()
async def list_tasks(context):
    """List all available tasks.
    Example: { "list_tasks": {} }
    """
    try:
        tasks = list_task_definitions()
        return json.dumps(tasks)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"

@command()
async def get_task_details(context, task_name: str):
    """Get details of a specific task.
    Example: { "get_task_details": { "task_name": "example_task" } }
    """
    try:
        task = get_task_definition(task_name)
        return json.dumps(task.dict())
    except FileNotFoundError:
        return f"Task '{task_name}' not found"
    except Exception as e:
        return f"Error getting task details: {str(e)}"

@command()
async def create_task(context, task_definition: dict):
    """Create a new task.
    Example: { "create_task": { "task_definition": { "name": "new_task", "description": "A new task", "user_input_fields": [], "output_schema": {} } } }
    """
    try:
        task = TaskDefinition(**task_definition)
        save_task_definition(task)
        return f"Task '{task.name}' created successfully"
    except Exception as e:
        return f"Error creating task: {str(e)}"

@command()
async def update_task(context, task_name: str, updated_definition: dict):
    """Update an existing task.
    Example: { "update_task": { "task_name": "existing_task", "updated_definition": { "description": "Updated description" } } }
    """
    try:
        task = get_task_definition(task_name)
        updated_task = TaskDefinition(**{**task.dict(), **updated_definition})
        update_task_definition(updated_task)
        return f"Task '{task_name}' updated successfully"
    except FileNotFoundError:
        return f"Task '{task_name}' not found"
    except Exception as e:
        return f"Error updating task: {str(e)}"

@command()
async def delete_task(context, task_name: str):
    """Delete a task.
    Example: { "delete_task": { "task_name": "task_to_delete" } }
    """
    try:
        delete_task_definition(task_name)
        return f"Task '{task_name}' deleted successfully"
    except FileNotFoundError:
        return f"Task '{task_name}' not found"
    except Exception as e:
        return f"Error deleting task: {str(e)}"

@command()
async def create_task_instance(context, task_name: str, user_id: str, input_values: dict, supervisor_agent_id: Optional[str] = None, chat_log_id: Optional[str] = None):
    """Create a new task instance.
    Example: { "create_task_instance": { "task_name": "example_task", "user_id": "user123", "input_values": {"param1": "value1"}, "supervisor_agent_id": "agent456", "chat_log_id": "chat789" } }
    """
    try:
        task_def = get_task_definition(task_name)
        instance = TaskInstance(
            id=str(uuid.uuid4()),
            task_definition=task_def,
            user_id=user_id,
            supervisor_agent_id=supervisor_agent_id,
            chat_log_id=chat_log_id,
            input_values=input_values,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        save_task_instance(instance)
        return f"Task instance '{instance.id}' created successfully"
    except Exception as e:
        return f"Error creating task instance: {str(e)}"

@command()
async def get_task_instance_details(context, instance_id: str):
    """Get details of a specific task instance.
    Example: { "get_task_instance_details": { "instance_id": "abc123" } }
    """
    try:
        instance = get_task_instance(instance_id)
        return json.dumps(instance.dict())
    except FileNotFoundError:
        return f"Task instance '{instance_id}' not found"
    except Exception as e:
        return f"Error getting task instance details: {str(e)}"

@command()
async def update_task_instance_status(context, instance_id: str, new_status: str):
    """Update the status of a task instance.
    Example: { "update_task_instance_status": { "instance_id": "abc123", "new_status": "COMPLETED" } }
    """
    try:
        instance = get_task_instance(instance_id)
        instance.status = TaskStatus(new_status)
        update_task_instance(instance)
        return f"Task instance '{instance_id}' status updated to {new_status}"
    except FileNotFoundError:
        return f"Task instance '{instance_id}' not found"
    except Exception as e:
        return f"Error updating task instance status: {str(e)}"

@command()
async def add_task_deliverable(context, instance_id: str, deliverable: dict):
    """Add a deliverable to a task instance.
    Example: { "add_task_deliverable": { "instance_id": "abc123", "deliverable": {"type": "document", "url": "https://example.com/doc.pdf"} } }
    """
    try:
        instance = get_task_instance(instance_id)
        instance.deliverables.append(deliverable)
        update_task_instance(instance)
        return f"Deliverable added to task instance '{instance_id}'"
    except FileNotFoundError:
        return f"Task instance '{instance_id}' not found"
    except Exception as e:
        return f"Error adding deliverable to task instance: {str(e)}"
