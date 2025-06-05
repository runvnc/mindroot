import os
import json

SESSION_DATA_DIR = "data/sessions"


async def save_session_data(session_id: str, property: str, value: str):
    name = f"{SESSION_DATA_DIR}/{session_id}/data.json"
    print(f"Saving session data: {session_id} {property} {value}")
    print("File name: ", name)
    # check for existing file
    # if not, create it
    if not os.path.exists(name):
        os.makedirs(os.path.dirname(name), exist_ok=True)
        with open(name, "w") as f:
            f.write("{}")
    # load existing data
    data = json.load(open(name))
    # update data
    data[property] = value
    # save data
    with open(name, "w") as f:
        f.write(json.dumps(data))


async def load_session_data(session_id: str, property: str):
    name = f"{SESSION_DATA_DIR}/{session_id}/data.json"
    print(f"Loading session data: {session_id} {property}")
    print("File name: ", name)
    # check for existing file
    # if not, create it
    if not os.path.exists(name):
        print("Session data file not found, returning None")
        return None
    # load existing data
    data = json.load(open(name))
    # return data
    return data.get(property, None)
