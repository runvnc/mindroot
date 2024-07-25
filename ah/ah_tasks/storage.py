import json
import os
from .models import TaskDefinition

TASK_DIR = '/files/ah/data/tasks'

def ensure_task_dir():
    os.makedirs(TASK_DIR, exist_ok=True)

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
