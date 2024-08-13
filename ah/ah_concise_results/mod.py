from ..services import service
from ..pipe import pipe


@pipe(name='process_results', priority=5)
def add_current_time(data: dict, context=None) -> dict:
    # iterate over all results 
    # for each object
    # look for 'say' or 'json_encoded_markdown'
    ret = [] 
    for result in data['results']:
        cmd, args = result['cmd'], result['args']
        if cmd == 'say' or cmd == 'json_encoded_markdown':
            ret.append(result)
        else:
            # we need to make sure the result['result'] is not too long
            # it could be a dict, list, or string.. but whatever it is we need to
            # ensure it is less than 18000 characters coming out of  the pipe
            ret.append(result)
    data['results'] = data['results']
    return data


