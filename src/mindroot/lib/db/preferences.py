import logging
from typing import List, Dict, Optional
from mindroot.registry import data_access

async def load_models() -> Optional[Dict]:
    try:
        models = data_access.read_models()
    except Exception as e:
        logging.error(f'Error reading model file: {e}')
        return None
    return models

async def load_provider_data() -> Optional[Dict]:
    try:
        provider_data = data_access.read_providers()
    except Exception as e:
        logging.error(f'Error reading provider data file: {e}')
        return None
    return provider_data

async def find_preferred_models(service_or_command_name: str, flags: List[str]) -> Optional[List[Dict]]:
    if not isinstance(service_or_command_name, str) or not service_or_command_name:
        logging.error('Invalid service_or_command_name')
        return None
    if not isinstance(flags, list) or not all((isinstance(flag, str) for flag in flags)):
        logging.error('Invalid flags')
        return None
    try:
        settings = data_access.read_preferred_models()
    except Exception as e:
        logging.error(f'Error reading settings file: {e}')
        return None
    matching_models = []
    settings = [setting for setting in settings if setting['service_or_command_name'] == service_or_command_name]
    for setting in settings:
        if setting['flag'] in flags:
            matching_models.append(setting)
    if not matching_models:
        return None
    providers = await load_provider_data()
    models = await load_models()
    for model in matching_models:
        for provider in providers:
            for provider_model in provider['models']:
                if provider_model['name'] == model['model']:
                    model['provider'] = provider['plugin']
                    model.update(provider_model)
                    for model_entry in models:
                        if model['name'] == model['model']:
                            model.update(model_entry)
                            break
                    if 'meta' in model:
                        model.update(model['meta'])
    logging.debug(f'Matching models found: {matching_models}')
    return matching_models