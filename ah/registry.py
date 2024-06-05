import asyncio
import json


async def select_models(provider=None, model_id=None, local=True, uncensored=False, service_or_command_name=None, flags=[]):
    type = service_or_command_name
    with open('data/models.json', 'r') as models_file:
        models = json.load(models_file)
    
    with open('data/providers.json', 'r') as providers_file:
        providers = json.load(providers_file)
    
    filtered_models = []
    
    for model in models:
        print(model, model_id, local, uncensored, type)
        if type and model['type'] != type:
            continue
        if uncensored and not model['uncensored']:
            continue
        if model_id is not None and model['name'] != model_id:
            continue
        print(3)
        for provider_entry in providers:
            print(3.5)
            if provider and provider_entry['name'] != provider:
                continue
            if local and not provider_entry['local']:
                continue
            print(4) 
            for provider_model in provider_entry['models']:
                print(5)
                if provider_model['name'] == model['name']:
                    print(6)
                    model_with_meta = model.copy()
                    model_with_meta.update(provider_model['meta'])
                    model['provider'] = provider_entry
                    filtered_models.append(model_with_meta)
                    break
    if len(filtered_models) == 0:
        print('No models found matching the criteria.', f"model_id: {model_id}", f"local: {local}", f"uncensored: {uncensored}", f"type: {type}")
    return filtered_models

