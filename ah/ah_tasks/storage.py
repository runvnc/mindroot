import json
import os
from .models import TaskDefinition, TaskInstance
from typing import List, Optional
import uuid
from datetime import datetime

TASK_DIR = '/files/ah/data/tasks'
TASK_INSTANCE_DIR = '/files/ah/data/task_instances'

def ensure_task_dir():
    os.makedirs(TASK_DIR, exist_ok=True)

def ensure_task_instance_dir():
    os.makedirs(TASK_INSTANCE_DIR, exist_ok=True)

def save_task_definition(task: TaskDefinition):
    ensure_task_dir()
    filename = f"{task.name}.json"
    filepath = os.path.join(TASK_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(task.dict(), f, indent=2)

def get_task_definition(name: str) -> TaskDefinition:
    filename = f"{name}.json"
    filepath = os.path.join(TASK_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Task definition '{name}' not found")
    with open(filepath, 'r') as f:
        data = json.load(f)
    return TaskDefinition(**data)

def list_task_definitions() -> list[str]:
    ensure_task_dir()
    return [f.split('.')[0] for f in os.listdir(TASK_DIR) if f.endswith('.json')]

def update_task_definition(task: TaskDefinition):
    save_task_definition(task)  # Overwrite existing file

def delete_task_definition(name: str):
    filename = f"{name}.json"
    filepath = os.path.join(TASK_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        raise FileNotFoundError(f"Task definition '{name}' not found")

def save_task_instance(task_instance: TaskInstance):
    ensure_task_instance_dir()
    filename = f"{task_instance.id}.json"
    filepath = os.path.join(TASK_INSTANCE_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(task_instance.dict(), f, indent=2)

def get_task_instance(instance_id: str) -> TaskInstance:
    filename = f"{instance_id}.json"
    filepath = os.path.join(TASK_INSTANCE_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Task instance '{instance_id}' not found")
    with open(filepath, 'r') as f:
        data = json.load(f)
    return TaskInstance(**data)

def list_task_instances(user_id: Optional[str] = None) -> List[str]:
    ensure_task_instance_dir()
    instances = [f.split('.')[0] for f in os.listdir(TASK_INSTANCE_DIR) if f.endswith('.json')]
    if user_id:
        return [instance_id for instance_id in instances if get_task_instance(instance_id).user_id == user_id]
    return instances

def update_task_instance(task_instance: TaskInstance):
    task_instance.updated_at = datetime.now().isoformat()
    save_task_instance(task_instance)

def delete_task_instance(instance_id: str):
    filename = f"{instance_id}.json"
    filepath = os.path.join(TASK_INSTANCE_DIR, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    else:
        raise FileNotFoundError(f"Task instance '{instance_id}' not found")
