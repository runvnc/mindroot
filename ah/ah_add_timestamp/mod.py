import re
from ..services import service
from ..hooks import hook, hook_manager
from ..pipe import pipe
import datetime

@pipe(name='pre_process_msg', priority=10)
def add_current_time(data: dict, context=None) -> dict:
    # format date time like MM/DD HH:MM AM/PM
    current_time = datetime.datetime.now().strftime('%m/%d %I:%M %p')
    data['message'] = f"[{current_time}]: {data['message']}"
    return data

