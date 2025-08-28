from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict
import json
import os
import sys
import traceback
from lib.providers.commands import command, command_manager
from lib.providers import services
from lib.providers.commands import command_manager
from lib.db.organize_models import organize_for_display
from copy import deepcopy
from .service_models import get_service_models_from_providers

# Import the new v2 preferences system with try/except for backward compatibility
try:
    from lib.providers.model_preferences_v2 import ModelPreferencesV2
except ImportError:
    ModelPreferencesV2 = None

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

class Setting(BaseModel):
    service_or_command_name: str
    flag: str
    model: str

@router.get('/settings', response_model=List[Dict])
async def get_settings():
    return read_settings()

@router.post('/settings')
async def save_settings(request: Request):
    try:
        body = await request.json()
        print(f"Received raw body: {body}")
        
        if isinstance(body, dict) and 'settings' in body:
            settings = [Setting(**item) for item in body['settings']]
        elif isinstance(body, list):
            settings = [Setting(**item) for item in body]
        else:
            raise ValueError("Invalid data format")
        
        print(f"Parsed settings: {settings}")
        write_settings([s.dict() for s in settings])
        return settings
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))

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

@router.get('/commands', response_model=Dict)
async def get_commands():
    print("retrieving commands")
    print(f"settings_router: command_manager instance ID: {id(command_manager)}")
    #funcs = command_manager.get_functions()
    funcs = command_manager.get_detailed_functions()
    print("funcs is")
    print(funcs)
    # we need to clone and remove the 'implementation' key which can't be serialized
    commands = deepcopy(funcs)
    
    for cmd_name, providers_list in commands.items():
        for provider in providers_list:
            if 'implementation' in provider:
                del provider['implementation']

    return commands

@router.get('/services', response_model=List[str])
async def get_services():
    return service_manager.get_functions()



#serviceModels will look like:
#{ "stream_chat": { 
#    "ah_openai": ["gpt-4o", "gpt-4.1-latest"],
#    "ah_anthropic": ["claude-3", "claude-2"]
#},
#{ "text_to_image": {
#  "ah_flux": ["flux-dev", "flux-pro"]
#}


@router.get('/service-models', response_model=Dict[str, Dict[str, List[str]]])
async def get_service_models():
    # Call get_service_models() on each provider and aggregate the results
    print("getting service models")
    service_models = await get_service_models_from_providers()
    return service_models


@router.get('/organized_models', response_model=List[Dict])
async def get_organized_models():
    models = read_models()
    providers = read_providers()
    equivalent_flags = read_equivalent_flags()
    return organize_for_display(models, providers, equivalent_flags)

@router.get('/equivalent_flags', response_model=List[List[str]])
async def get_equivalent_flags():
    return read_equivalent_flags()

# NEW V2 ENDPOINTS - These are additive and don't affect existing functionality

@router.get('/settings_v2', response_model=Dict[str, List[List[str]]])
async def get_settings_v2():
    """Get preferences in new v2 format: {service: [[provider, model], ...]}"""
    if ModelPreferencesV2 is None:
        raise HTTPException(status_code=501, detail="Model Preferences V2 not available")
    
    try:
        prefs_manager = ModelPreferencesV2()
        return prefs_manager.get_preferences()
    except Exception as e:
        trace = traceback.format_exc()
        print(f"Error getting v2 preferences: {e}\n\n{trace}")
        print(e)
        print(trace)
        sys.exit(1)
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/settings_v2')
async def save_settings_v2(request: Request):
    """Save preferences in new v2 format."""
    if ModelPreferencesV2 is None:
        raise HTTPException(status_code=501, detail="Model Preferences V2 not available")
    
    try:
        body = await request.json()
        print(f"Received v2 preferences: {body}")
        
        # Validate format: should be {service: [[provider, model], ...]}
        if not isinstance(body, dict):
            raise ValueError("Preferences must be a dictionary")
        
        for service, provider_model_pairs in body.items():
            if not isinstance(provider_model_pairs, list):
                raise ValueError(f"Service '{service}' must have a list of provider/model pairs")
            
            for pair in provider_model_pairs:
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError(f"Each provider/model pair must be a list of exactly 2 items")
                if not all(isinstance(item, str) for item in pair):
                    raise ValueError(f"Provider and model names must be strings")
        
        prefs_manager = ModelPreferencesV2()
        prefs_manager.save_preferences(body)
        
        return {"success": True, "message": "Preferences saved successfully"}
        
    except Exception as e:
        print(f"Error saving v2 preferences: {e}")
        raise HTTPException(status_code=422, detail=str(e))

@router.post('/migrate_settings')
async def migrate_settings():
    """One-time migration from old format to new v2 format."""
    if ModelPreferencesV2 is None:
        raise HTTPException(status_code=501, detail="Model Preferences V2 not available")
    
    try:
        # Get old format preferences
        old_preferences = read_settings()
        
        # Convert to new format
        prefs_manager = ModelPreferencesV2()
        new_preferences = prefs_manager.migrate_from_old_format(old_preferences)
        
        # Save new format
        prefs_manager.save_preferences(new_preferences)
        
        return {
            "success": True, 
            "message": f"Migrated {len(old_preferences)} old preferences to new format",
            "migrated_preferences": new_preferences
        }
        
    except Exception as e:
        print(f"Error migrating preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
