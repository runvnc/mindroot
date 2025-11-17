import os
import json
SESSION_DATA_DIR = 'data/sessions'

async def save_session_data(session_id: str, property: str, value: str):
    name = f'{SESSION_DATA_DIR}/{session_id}/data.json'
    if not os.path.exists(name):
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, 'w') as f:
            f.write('{}')
    data = json.load(open(name))
    data[property] = value
    with open(name, 'w') as f:
        f.write(json.dumps(data))

async def load_session_data(session_id: str, property: str):
    name = f'{SESSION_DATA_DIR}/{session_id}/data.json'
    if not os.path.exists(name):
        return None
    data = json.load(open(name))
    return data.get(property, None)