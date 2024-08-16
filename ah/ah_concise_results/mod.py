import json
from ..services import service
from ..pipe import pipe

def truncate_if_needed(obj, max_length, current_depth=0, max_depth=3):
    TRUNCATION_INDICATOR = '... (truncated)'
    
    if current_depth > max_depth:
        return f"{{Truncated due to depth. Type: {type(obj).__name__}}}"
    
    if isinstance(obj, dict):
        result = {}
        remaining_length = max_length
        for key, value in obj.items():
            truncated_value = truncate_if_needed(value, remaining_length, current_depth + 1, max_depth)
            result[key] = truncated_value
            remaining_length -= len(json.dumps({key: truncated_value}))
            if remaining_length <= 0:
                result[key] = TRUNCATION_INDICATOR
                break
        return result
    elif isinstance(obj, list):
        result = []
        remaining_length = max_length
        for item in obj:
            truncated_item = truncate_if_needed(item, remaining_length, current_depth + 1, max_depth)
            result.append(truncated_item)
            remaining_length -= len(json.dumps(truncated_item)) + 2  # +2 for brackets and comma
            if remaining_length <= 0:
                result.append(TRUNCATION_INDICATOR)
                break
        return result
    elif isinstance(obj, str):
        if len(obj) > max_length:
            return obj[:max_length - len(TRUNCATION_INDICATOR)] + TRUNCATION_INDICATOR
    return obj

@pipe(name='truncate_results', priority=5)
def truncate_long_results(data: dict, context=None) -> dict:
    RESULT_MAX_LENGTH = 18000
    ARGS_MAX_LENGTH = 3000

    processed_results = []
    for result in data['results']:
        cmd = result['cmd']
        if cmd in ['say', 'json_encoded_markdown']:
            processed_results.append(result)
        else:
            if 'result' in result:
                result['result'] = truncate_if_needed(result['result'], RESULT_MAX_LENGTH)
            if 'args' in result:
                result['args'] = truncate_if_needed(result['args'], ARGS_MAX_LENGTH)
            processed_results.append(result)

    data['results'] = processed_results
    return data
