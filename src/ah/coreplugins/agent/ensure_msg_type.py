def ensure_has_type(command):
    if not isinstance(command, dict):
        return {
            "type": "text",
            "text": str(command)
        }
    if not 'type' in command:
        command['type'] = 'text'
    return command


