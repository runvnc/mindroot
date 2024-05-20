import asyncio


# models.json
[
  {
    "type": "sd",
    "subtype": "SDXL",
    "name": "mklan-x-real",
    "uncensored": true,
    "description": "SDXL-Hyper, Very NSFW, strong prompt adherance.",
  }
]

# providers.json 
[
  "name": "AH Runpod",
  "local": false,
  "plugin": "ah_runpod_sd",
  "models": [ 
      "name": "mklan-x-real",
      "meta": { "endpoint_id": "b6kn2n72y7aooe" }
    }
  ]
]

import json

async def get_models(provider=None, local=True, uncensored=False, type=None):
    with open('data/models.json', 'r') as models_file:
        models = json.load(models_file)
    
    with open('data/providers.json', 'r') as providers_file:
        providers = json.load(providers_file)
    
    filtered_models = []
    
    for model in models:
        if type and model['type'] != type:
            continue
        if uncensored and not model['uncensored']:
            continue
        
        for provider_entry in providers:
            if provider and provider_entry['name'] != provider:
                continue
            if local and not provider_entry['local']:
                continue
            
            for provider_model in provider_entry['models']:
                if provider_model['name'] == model['name']:
                    filtered_models.append(model)
                    break
    
    return filtered_models
