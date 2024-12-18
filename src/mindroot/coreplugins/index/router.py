import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile
from .models import IndexMetadata, PluginEntry, AgentEntry
from .handlers import (
    list_indices, create_index, update_index,
    add_plugin, remove_plugin,
    add_agent, remove_agent,
    publish_index, install_index_from_zip
)

router = APIRouter()

ORIGINAL_WORKING_DIR = os.getcwd()
INDEX_DIR = Path(ORIGINAL_WORKING_DIR) / 'indices'
PUBLISHED_DIR = Path(ORIGINAL_WORKING_DIR) / 'published_indices'

# Ensure directories exist
os.makedirs(INDEX_DIR, exist_ok=True)
os.makedirs(PUBLISHED_DIR, exist_ok=True)

@router.get("/index/list-indices")
async def list_indices_route():
    return await list_indices(INDEX_DIR)

@router.post("/index/create-index")
async def create_index_route(metadata: IndexMetadata):
    return await create_index(INDEX_DIR, metadata)

@router.post("/index/update-index/{index_name}")
async def update_index_route(index_name: str, metadata: IndexMetadata):
    return await update_index(INDEX_DIR, index_name, metadata)

@router.post("/index/add-plugin/{index_name}")
async def add_plugin_route(index_name: str, plugin: PluginEntry):
    return await add_plugin(INDEX_DIR, index_name, plugin)

@router.delete("/index/remove-plugin/{index_name}/{plugin_name}")
async def remove_plugin_route(index_name: str, plugin_name: str):
    return await remove_plugin(INDEX_DIR, index_name, plugin_name)

@router.post("/index/add-agent/{index_name}")
async def add_agent_route(index_name: str, agent: AgentEntry):
    return await add_agent(INDEX_DIR, index_name, agent)

@router.delete("/index/remove-agent/{index_name}/{agent_name}")
async def remove_agent_route(index_name: str, agent_name: str):
    return await remove_agent(INDEX_DIR, index_name, agent_name)

@router.post("/index/publish/{index_name}")
async def publish_index_route(index_name: str):
    return await publish_index(INDEX_DIR, PUBLISHED_DIR, index_name)

@router.post("/index/install-zip")
async def install_index_route(file: UploadFile = File(...)):
    return await install_index_from_zip(INDEX_DIR, file)
