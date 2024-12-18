from typing import List, Dict, Optional
from termcolor import colored
from mindroot.registry import data_access

# Load equivalent flags
def load_equivalent_flags() -> List[List[str]]:
    return data_access.read_equivalent_flags()

# Organize models and providers for display
def organize_for_display(models: List[Dict], providers: List[Dict], equivalent_flags: List[List[str]]) -> List[Dict]:
    organized_data = []
    service_dict = {}
    flag_mapping = {flag: eq_flag[0] for eq_flag in equivalent_flags for flag in eq_flag}

    for provider in providers:
        for model in provider['models']:
            model_info = next((m for m in models if m['name'] == model['name']), None)
            if model_info:
                for service in model['services']:
                    if service not in service_dict:
                        service_dict[service] = {}
                    matched_flag = False
                    for flag in model_info['flags']:
                        equivalent_flag = flag_mapping.get(flag, flag)
                        if equivalent_flag not in service_dict[service]:
                            service_dict[service][equivalent_flag] = []
                        
                        service_dict[service][equivalent_flag].append({
                            'provider': provider,
                            'model': model_info,
                            'type': model_info['type'],
                            'subtype': model_info['subtype'],
                            'available': model['available']
                        })
                        matched_flag = True
                    if not matched_flag:
                        if 'no_flags' not in service_dict[service]:
                            service_dict[service]['no_flags'] = []
                        service_dict[service]['no_flags'].append({
                            'provider': provider,
                            'model': model_info,
                            'type': model_info['type'],
                            'subtype': model_info['subtype'],
                            'available': model['available']
                        })

    for service, flags in service_dict.items():
        organized_data.append({
            'service': service,
            'flags': [
                {'flag': flag, 'models': models} for flag, models in flags.items()
            ]
        })

    return organized_data

async def load_organized():
    models = data_access.read_models()
    providers = data_access.read_providers()
    plugins = data_access.read_plugins()
    
    providers = [provider for provider in providers if any(provider['plugin'] == plugin['name'] and plugin['enabled'] for plugin in plugins)]

    equivalent_flags = load_equivalent_flags()
    return organize_for_display(models, providers, equivalent_flags)

async def uses_models(service_or_command_name: str) -> bool:
    if not isinstance(service_or_command_name, str) or not service_or_command_name:
        logging.error('Invalid service_or_command_name')
        raise ValueError('Invalid service_or_command_name')
    organized_data = await load_organized()
    for service in organized_data:
        if service['service'] == service_or_command_name:
            return True
    return False

async def matching_models(service_or_command_name: str, flags: List[str]) -> Optional[List[Dict]]:
    if not isinstance(service_or_command_name, str) or not service_or_command_name:
        logging.error('Invalid service_or_command_name')
        return None
    if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
        logging.error('Invalid flags')
        return None

    if len(flags) == 0:
        flags = ['no_flags']
    organized_data = await load_organized()
    # find all models that match the given service_or_command_name and equivalent_flags
    matching_models = []
    for service in organized_data:
        if service['service'] == service_or_command_name:
            for flag in service['flags']:
                if flag['flag'] in flags:
                    for entry in flag['models']:
                        result = {}  
                        models = entry['provider']['models']
                        available_models = [model for model in models if model['available']]
                        if len(available_models) > 0:
                            result.update(available_models[0])
                            result['provider'] = entry['provider']['plugin']
                            result.update(entry['model'])
                            if 'meta' in result:
                                result.update(result['meta'])

                            matching_models.append(result)
    return matching_models

if __name__ == '__main__':
    models = data_access.read_models()
    providers = data_access.read_providers()
    equivalent_flags = load_equivalent_flags()
    organized_data = organize_for_display(models, providers, equivalent_flags)
