import json
import os
from ..services import service
from ..pipe import pipe

@pipe(name='filter_messages', priority=8)
def truncate_long_results(data: dict, context=None) -> dict:
    max_context = int(os.getenv('AH_MAX_CONTEXT', 64000))
    messages = data['messages']
    
    if len(messages) <= 3:
        return data
    
    # Store the role of the last message
    last_role = messages[-1]['role']
    
    # Always keep the first 3 messages (system, user, assistant)
    processed_results = messages[:3]
    total_length = sum(len(msg['content']) for msg in processed_results)
    
    # Process remaining messages, ensuring alternating roles
    i = 3
    while i < len(messages):
        if i + 1 < len(messages):
            user_msg, assistant_msg = messages[i], messages[i+1]
            
            # Ensure the pair is user-assistant
            if user_msg['role'] == 'user' and assistant_msg['role'] == 'assistant':
                pair_length = len(user_msg['content']) + len(assistant_msg['content'])
                
                if total_length + pair_length <= max_context:
                    processed_results.extend([user_msg, assistant_msg])
                    total_length += pair_length
                    i += 2
                else:
                    break  # Stop processing if we exceed max_context
            else:
                # If roles are not alternating, skip to the next potential pair
                i += 1
        else:
            # If there's an odd number of messages, check if we can add the last one
            last_msg = messages[i]
            if last_msg['role'] != processed_results[-1]['role']:
                if total_length + len(last_msg['content']) <= max_context:
                    processed_results.append(last_msg)
            break
    
    # Ensure the last role matches the original last role
    if processed_results[-1]['role'] != last_role:
        if len(processed_results) > 3 and total_length - len(processed_results[-1]['content']) + len(messages[-1]['content']) <= max_context:
            # Remove the last processed message and add the original last message
            total_length -= len(processed_results.pop()['content'])
            processed_results.append(messages[-1])
        elif total_length + len(messages[-1]['content']) <= max_context:
            # If there's room, just add the original last message
            processed_results.append(messages[-1])
    
    data['messages'] = processed_results
    return data
