import json
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

async def find_preferred_models(service_or_command_name: str, flags: List[str], settings_file_path: str = 'data/preferred_models.json') -> Optional[List[Dict]]:
    if not isinstance(service_or_command_name, str) or not service_or_command_name:
        logging.error('Invalid service_or_command_name')
        return None
    if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
        logging.error('Invalid flags')
        return None

    try:
        with open(settings_file_path, 'r') as settings_file:
            pass
    except FileNotFoundError:
        with open(settings_file_path, 'w') as settings_file:
            json.dump([], settings_file)

    try:
        with open(settings_file_path, 'r') as settings_file:
            settings = json.load(settings_file)
    except Exception as e:
        logging.error(f'Error reading settings file: {e}')
        return None

    matching_models = []

    for setting in settings:
        print("setting: ", setting)
        if setting['service_or_command_name'] != service_or_command_name:
            continue

        positive_flags = set(setting['positive_flags'])
        negative_flags = set(setting['negative_flags'])
        input_flags = set(flags)

        if positive_flags.issubset(input_flags) and negative_flags.isdisjoint(input_flags):
            matching_models.append(setting)

    if not matching_models:
        logging.info('No matching models found')
        return None

    logging.info(f'Matching models found: {matching_models}')
    return matching_models



