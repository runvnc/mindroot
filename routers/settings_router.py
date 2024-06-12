from fastapi import APIRouter, HTTPException
from typing import List, Dict
import json
import os
from ah.commands import command_manager
from ah.services import service_manager
from ah.organize_models import organize_for_display

router = APIRouter()

SETTINGS_FILE_PATH = 'data/preferred_models.json'
MODELS_FILE_PATH = 'data/models.json'
PROVIDERS_FILE_PATH = 'data/providers.json'
EQUIVALENT_FLAGS_FILE_PATH = 'data/equivalent_flags.json'

# Helper function to read settings file
def read_settings() -> List[Dict]:
    if not os.path.exists(SETTINGS_FILE_PATH):
        return []
    with open(SETTINGS_FILE_PATH, 'r') as settings_file:
        return json.load(settings_file)

# Helper function to write settings file
def write_settings(settings: List[Dict]):
    with open(SETTINGS_FILE_PATH, 'w') as settings_file:
        json.dump(settings, settings_file, indent=4)

# Helper function to read models file
def read_models() -> List[Dict]:
    if not os.path.exists(MODELS_FILE_PATH):
        return []
    with open(MODELS_FILE_PATH, 'r') as models_file:
        return json.load(models_file)

# Helper function to read providers file
def read_providers() -> List[Dict]:
    if not os.path.exists(PROVIDERS_FILE_PATH):
        return []
    with open(PROVIDERS_FILE_PATH, 'r') as providers_file:
        return json.load(providers_file)

# Helper function to read equivalent flags file
def read_equivalent_flags() -> List[List[str]]:
    if not os.path.exists(EQUIVALENT_FLAGS_FILE_PATH):
        print("No equivalent flags file found")
        print("Looked in " + EQUIVALENT_FLAGS_FILE_PATH)
        return []
    with open(EQUIVALENT_FLAGS_FILE_PATH, 'r') as equivalent_flags_file:
        return json.load(equivalent_flags_file)

@router.get('/settings', response_model=List[Dict])
async def get_settings():
    return read_settings()

@router.post('/settings', response_model=Dict)
async def save_settings(settings: list):
    write_settings(settings)
    return setting

@router.put('/settings/{setting_id}', response_model=Dict)
async def update_setting(setting_id: int, updated_setting: Dict):
    settings = read_settings()
    if setting_id < 0 or setting_id >= len(settings):
        raise HTTPException(status_code=404, detail='Setting not found')
    settings[setting_id] = updated_setting
    write_settings(settings)
    return updated_setting

@router.delete('/settings/{setting_id}', response_model=Dict)
async def delete_setting(setting_id: int):
    settings = read_settings()
    if setting_id < 0 or setting_id >= len(settings):
        raise HTTPException(status_code=404, detail='Setting not found')
    deleted_setting = settings.pop(setting_id)
    write_settings(settings)
    return deleted_setting

@router.get('/models', response_model=List[Dict])
async def get_models():
    return read_models()

@router.get('/providers', response_model=List[Dict])
async def get_providers():
    return read_providers()

@router.get('/commands', response_model=List[str])
async def get_commands():
    print("retrieving commands")
    funcs = command_manager.get_functions()
    print(funcs)
    return funcs

@router.get('/services', response_model=List[str])
async def get_services():
    return service_manager.get_functions()

@router.get('/organized_models', response_model=List[Dict])
async def get_organized_models():
    models = read_models()
    providers = read_providers()
    equivalent_flags = read_equivalent_flags()
    return organize_for_display(models, providers, equivalent_flags)

@router.get('/equivalent_flags', response_model=List[List[str]])
async def get_equivalent_flags():
    return read_equivalent_flags()

