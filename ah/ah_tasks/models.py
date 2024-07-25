from pydantic import BaseModel, Field
from typing import Dict, Any, List, Union

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
