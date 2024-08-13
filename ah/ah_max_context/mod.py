import json
import os
from ..services import service
from ..pipe import pipe

@pipe(name='filter_messages', priority=8)
def truncate_long_results(data: dict, context=None) -> dict:
    max_context = int(os.getenv('AH_MAX_CONTEXT', 64000))
    messages = data['messages']
    
    if len(messages) <= 7:  # 3 (start) + 4 (end)
        return data  # No truncation needed
    
    # Always keep the first 3 messages and last 4 messages
    start_messages = messages[:3]
    end_messages = messages[-4:]
    middle_messages = messages[3:-4]
    
    processed_results = start_messages.copy()
    total_length = sum(len(msg['content']) for msg in processed_results + end_messages)
    
    for i in range(0, len(middle_messages), 2):
        if i + 1 < len(middle_messages):  # Ensure we have a pair
            user_msg, assistant_msg = middle_messages[i], middle_messages[i+1]
            pair_length = len(user_msg['content']) + len(assistant_msg['content'])
            
            if total_length + pair_length <= max_context:
                processed_results.extend([user_msg, assistant_msg])
                total_length += pair_length
            else:
                break  # Stop processing if we exceed max_context
    
    # Add the last 4 messages, even if it exceeds max_context
    processed_results.extend(end_messages)
    
    data['messages'] = processed_results
    return data
