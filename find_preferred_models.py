import json
import logging
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)

async def find_preferred_models(service_or_command_name: str, flags: List[str], settings_file_path: str = 'data/preferred_models.json') -> Optional[List[Dict]]:
    # Validate input parameters
    if not isinstance(service_or_command_name, str) or not service_or_command_name:
        logging.error('Invalid service_or_command_name')
        return None
    if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
        logging.error('Invalid flags')
        return None

    try:
        # Step 1: Read the settings file
        with open(settings_file_path, 'r') as settings_file:
            settings = json.load(settings_file)
    except Exception as e:
        logging.error(f'Error reading settings file: {e}')
        return None

    # Step 2: Initialize variables
    matching_models = []

    # Step 3: Iterate through settings
    for setting in settings:
        if setting['service_or_command_name'] != service_or_command_name:
            continue

        # Step 4: Filter based on flags
        positive_flags = set(setting['positive_flags'])
        negative_flags = set(setting['negative_flags'])
        input_flags = set(flags)

        if positive_flags.issubset(input_flags) and negative_flags.isdisjoint(input_flags):
            matching_models.append(setting)

    # Step 5: Handle no matches
    if not matching_models:
        logging.info('No matching models found')
        return None

    # Step 6: Return matching models
    logging.info(f'Matching models found: {matching_models}')
    return matching_models
