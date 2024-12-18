from pydantic import BaseModel
from typing import List, Optional

class IndexMetadata(BaseModel):
    name: str
    description: Optional[str] = ""
    version: str = "1.0.0"
    url: Optional[str] = None
    trusted: bool = False

class PluginManifest(BaseModel):
    """Model for reading plugin manifest files"""
    name: str
    version: str
    description: Optional[str] = None
    commands: List[str]
    services: List[str] = []
    dependencies: List[str] = []

class PluginEntry(BaseModel):
    """Model for plugin entries in index"""
    name: str
    version: str
    description: Optional[str] = None
    source: str
    source_path: Optional[str] = None
    github_url: Optional[str] = None
    remote_source: Optional[str] = None
    commands: Optional[List[str]] = []  # Made optional again
    services: List[str] = []
    dependencies: List[str] = []

class AgentEntry(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    required_commands: List[str] = []
    required_services: List[str] = []
