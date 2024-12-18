import asyncio
from lib.db.registry import data_access

async def select_models(provider=None, model_id=None, local=True, uncensored=False, service_or_command=None, flags=[]):
    type = service_or_command
    models = data_access.read_models()
    providers = data_access.read_providers()
    
    filtered_models = []
    
    for model in models:
        if type and model['type'] != type:
            continue
        if uncensored and not model['uncensored']:
            continue
        if model_id is not None and model['name'] != model_id:
            continue
        
        for provider_entry in providers:
            if provider and provider_entry['name'] != provider:
                continue
            if local and not provider_entry['local']:
                continue
            
            for provider_model in provider_entry['models']:
                if provider_model['name'] == model['name']:
                    model_with_meta = model.copy()
                    model_with_meta.update(provider_model['meta'])
                    model['provider'] = provider_entry
                    filtered_models.append(model_with_meta)
                    break
    
    if len(filtered_models) == 0:
        print('No models found matching the criteria.', f"model_id: {model_id}", f"local: {local}", f"uncensored: {uncensored}", f"type: {type}")
    
    return filtered_models
