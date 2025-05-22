import os
import json
import re
import time
from typing import Dict, List
from mindroot.lib.chatlog import ChatLog

def find_chatlog_file(log_id: str) -> str:
    """
    Find a chatlog file by its log_id.
    
    Args:
        log_id: The log ID to search for
        
    Returns:
        The full path to the chatlog file if found, None otherwise
    """
    chat_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
    
    # Use os.walk to search through all subdirectories
    for root, dirs, files in os.walk(chat_dir):
        for file in files:
            if file == f"chatlog_{log_id}.json":
                return os.path.join(root, file)
    
    return None

def extract_delegate_task_log_ids(messages: List[Dict]) -> List[str]:
    """
    Extract log IDs from delegate_task commands in messages.
    
    Args:
        messages: List of chat messages
        
    Returns:
        List of log IDs found in delegate_task commands
    """
    log_ids = []
    
    for message in messages:
        if message['role'] == 'assistant':
            content = message['content']
            # Handle both string and list content formats
            if isinstance(content, str):
                text = content
            elif isinstance(content, list) and len(content) > 0 and 'text' in content[0]:
                text = content[0]['text']
            else:
                continue
                
            # Try to parse as JSON
            try:
                commands = json.loads(text)
                if not isinstance(commands, list):
                    commands = [commands]
                    
                for cmd in commands:
                    for key, value in cmd.items():
                        if key == 'delegate_task' and 'log_id' in value:
                            log_ids.append(value['log_id'])
            except (json.JSONDecodeError, TypeError, KeyError):
                # If not JSON, try regex to find log_ids in delegate_task commands
                matches = re.findall(r'"delegate_task"\s*:\s*{\s*"log_id"\s*:\s*"([^"]+)"', text)
                log_ids.extend(matches)
    
    return log_ids

def get_cache_dir() -> str:
    """
    Get the directory for token count cache files.
    Creates the directory if it doesn't exist.
    """
    cache_dir = os.environ.get('TOKEN_CACHE_DIR', 'data/token_cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return cache_dir

def get_cache_path(log_id: str) -> str:
    """
    Get the path to the cache file for a specific log_id.
    """
    cache_dir = get_cache_dir()
    return os.path.join(cache_dir, f"tokens_{log_id}.json")

def get_cached_token_counts(log_id: str, log_path: str) -> Dict[str, int]:
    """
    Get cached token counts if available and valid.
    
    Args:
        log_id: The log ID
        log_path: Path to the actual log file
        
    Returns:
        Cached token counts if valid, None otherwise
    """
    cache_path = get_cache_path(log_id)
    
    # If cache doesn't exist, return None
    if not os.path.exists(cache_path):
        return None
    
    try:
        # Get modification times
        log_mtime = os.path.getmtime(log_path)
        cache_mtime = os.path.getmtime(cache_path)
        current_time = time.time()
        
        # If log was modified after cache was created, cache is invalid
        if log_mtime > cache_mtime:
            return None
        
        # Don't recalculate sooner than 3 minutes after last calculation
        if current_time - cache_mtime < 180:  # 3 minutes in seconds
            with open(cache_path, 'r') as f:
                return json.load(f)
                
        # For logs that haven't been modified in over an hour, consider them "finished"
        # and use the cache regardless of when it was last calculated
        if current_time - log_mtime > 3600:  # 1 hour in seconds
            with open(cache_path, 'r') as f:
                return json.load(f)
    
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading token cache: {e}")
    
    return None

def save_token_counts_to_cache(log_id: str, token_counts: Dict[str, int]) -> None:
    """
    Save token counts to cache.
    """
    cache_path = get_cache_path(log_id)
    with open(cache_path, 'w') as f:
        json.dump(token_counts, f)

def count_tokens_for_log_id(log_id: str) -> Dict[str, int]:
    """
    Count tokens for a chat log identified by log_id, including any delegated tasks.
    
    Args:
        log_id: The log ID to count tokens for
        
    Returns:
        Dictionary with token counts or None if log not found
    """
    # Find the chatlog file
    chatlog_path = find_chatlog_file(log_id)
    if not chatlog_path:
        return None
    
    # Check cache first
    cached_counts = get_cached_token_counts(log_id, chatlog_path)
    if cached_counts:
        print(f"Using cached token counts for {log_id}")
        return cached_counts
    
    print(f"Calculating token counts for {log_id}")
    
    # Load the chat log
    with open(chatlog_path, 'r') as f:
        log_data = json.load(f)
        
    # Create a temporary ChatLog instance to count tokens
    temp_log = ChatLog(log_id=log_id, user="system", agent=log_data.get('agent', 'unknown'))
    temp_log.messages = log_data.get('messages', [])
    
    # Count tokens for this log
    parent_counts = temp_log.count_tokens()
    
    # Create combined counts (starting with parent counts)
    combined_counts = {}
    combined_counts['input_tokens_sequence'] = parent_counts['input_tokens_sequence']
    combined_counts['output_tokens_sequence'] = parent_counts['output_tokens_sequence']
    combined_counts['input_tokens_total'] = parent_counts['input_tokens_total']
    
    # Find delegated task log IDs
    delegated_log_ids = extract_delegate_task_log_ids(temp_log.messages)
    
    # Recursively count tokens for delegated tasks
    for delegated_id in delegated_log_ids:
        delegated_counts = count_tokens_for_log_id(delegated_id)
        if delegated_counts:
            combined_counts['input_tokens_sequence'] += delegated_counts['input_tokens_sequence']
            combined_counts['output_tokens_sequence'] += delegated_counts['output_tokens_sequence']
            combined_counts['input_tokens_total'] += delegated_counts['input_tokens_total']
    
    # Create final result with both parent and combined counts
    token_counts = {}
    # Parent session only counts
    token_counts['input_tokens_sequence'] = parent_counts['input_tokens_sequence']
    token_counts['output_tokens_sequence'] = parent_counts['output_tokens_sequence']
    token_counts['input_tokens_total'] = parent_counts['input_tokens_total']
    # Combined counts (parent + all subtasks)
    token_counts['combined_input_tokens_sequence'] = combined_counts['input_tokens_sequence']
    token_counts['combined_output_tokens_sequence'] = combined_counts['output_tokens_sequence']
    token_counts['combined_input_tokens_total'] = combined_counts['input_tokens_total']
    
    # Save to cache
    save_token_counts_to_cache(log_id, token_counts)
    
    return token_counts
