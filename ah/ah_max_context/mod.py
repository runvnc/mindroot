import json
from ..services import service
from ..pipe import pipe

@pipe(name='filter_messages', priority=8)
def truncate_long_results(data: dict, context=None) -> dict:
    processed_results = []
    for result in data['messages']:

    data['messages'] = processed_results
    return data
