from pydantic import BaseModel, Field
from typing import Dict, Any, List, Union, Optional
from enum import Enum

class FileUploadField(BaseModel):
    name: str
    description: str
    required: bool = True
    allowed_extensions: List[str]

class FormField(BaseModel):
    name: str
    description: str
    type: str
    required: bool = True

class AdminFileUpload(BaseModel):
    name: str
    description: str
    file_path: str
    allowed_extensions: List[str]

class TaskDefinition(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")
    user_input_fields: List[Union[FormField, FileUploadField]] = Field(..., description="List of user input fields including form fields and file uploads")
    admin_input_files: List[AdminFileUpload] = Field(default=[], description="List of admin-uploaded input files")
    output_schema: Dict[str, Any] = Field(..., description="JSON schema for task outputs")

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class TaskInstance(BaseModel):
    id: str = Field(..., description="Unique identifier for the task instance")
    task_definition: TaskDefinition
    user_id: str = Field(..., description="ID of the user associated with this task instance")
    supervisor_agent_id: Optional[str] = Field(None, description="ID of the supervisor agent, if any")
    chat_log_id: Optional[str] = Field(None, description="ID of the associated agent chat log, if any")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task instance")
    input_values: Dict[str, Any] = Field(..., description="Input values provided for this task instance")
    deliverables: List[Dict[str, Any]] = Field(default=[], description="List of deliverables produced by this task instance")
    created_at: str = Field(..., description="Timestamp of when the task instance was created")
    updated_at: str = Field(..., description="Timestamp of the last update to the task instance")
