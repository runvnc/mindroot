from fastapi import APIRouter, HTTPException
from typing import List, Dict
import json
import os

router = APIRouter()

SETTINGS_FILE_PATH = 'data/preferred_models.json'

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

@router.get('/settings', response_model=List[Dict])
async def get_settings():
    return read_settings()

@router.post('/settings', response_model=Dict)
async def add_setting(setting: Dict):
    settings = read_settings()
    settings.append(setting)
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
