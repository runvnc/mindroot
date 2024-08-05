import re
from ..services import service
from ..hooks import hook, hook_manager
from ..pipe import pipe

@pipe(name='pre_process_msg', priority=10)
def spaces_jailbreak(data: dict, context=None) -> dict:
    data['message'] = ' '.join(data['message'])
    return data


@pipe(name='before_store_msg', priority=1)
def store_msg(data: dict, context=None) -> dict:
    # remove extra spaces
    data['message'] = re.sub(' +', ' ', data['message'])
    return data

