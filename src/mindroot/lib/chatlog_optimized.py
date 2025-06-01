import os
import json
from typing import List, Dict, Set, Optional, Tuple
import sys
import traceback
import re
import time
from mindroot.lib.utils.debug import debug_box
from collections import defaultdict
import threading

# Global cache for directory structure and parent-child relationships
_log_index_cache = {
    'log_paths': {},  # log_id -> full_path
    'parent_children': defaultdict(set),  # parent_log_id -> set of child_log_ids
    'log_metadata': {},  # log_id -> {parent_log_id, agent, user, mtime}
    'last_scan': 0,
    'scan_lock': threading.Lock()
}

class ChatLog:
    def __init__(self, log_id=0, agent=None, parent_log_id=None, context_length: int = 4096, user: str = None):
        self.log_id = log_id
        self.messages = []
        self.parent_log_id = parent_log_id
        self.agent = agent
        if user is None or user == '' or user == 'None':
            raise ValueError('User must be provided')
        # make sure user is string
        if not isinstance(user, str):
            # does it have a username?
            if hasattr(user, 'username'):
                user = user.username
            else:
                # throw an error
                raise ValueError('ChatLog(): user must be a string or have username field')
        self.user = user
        if agent is None or agent == '':
            raise ValueError('Agent must be provided')
        self.context_length = context_length
        self.log_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
        self.log_dir = os.path.join(self.log_dir, self.user)
        self.log_dir = os.path.join(self.log_dir, self.agent)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.load_log()
        
    def _get_log_data(self) -> Dict[str, any]:
        return {
            'agent': self.agent,
            'log_id': self.log_id,
            'messages': self.messages,
            'parent_log_id': self.parent_log_id
        }

    def _calculate_message_length(self, message: Dict[str, str]) -> int:
        return len(json.dumps(message)) // 3

    def add_message(self, message: Dict[str, str]) -> None:
        if len(self.messages)>0 and self.messages[-1]['role'] == message['role']:
            print("found repeat role")
            # check if messasge is str
            # if so, convert to dict with type 'text':
            if type(message['content']) == str:
                message['content'] = [{'type':'text', 'text': message['content']}]
            elif type(message['content']) == list:
                for part in message['content']:
                    if part['type'] == 'image':
                        print("found image")
                        self.messages.append(message)
                        self.save_log()
                        return

            try:
                cmd_list = json.loads(self.messages[-1]['content'][0]['text'])
                if type(cmd_list) != list:
                    debug_box("1")
                    cmd_list = [cmd_list]
                new_json = json.loads(message['content'][0]['text'])
                if type(new_json) != list:
                    debug_box("2")
                    new_json = [new_json]
                new_cmd_list = cmd_list + new_json
                debug_box("3")
                self.messages[-1]['content'] = [{ 'type': 'text', 'text': json.dumps(new_cmd_list) }]
            except Exception as e:
                # assume previous mesage was not a command, was a string
                debug_box("4")
                print("Could not combine commands, probably normal if user message and previous system output, assuming string", e)
                if type(self.messages[-1]['content']) == str:
                    new_msg_text = self.messages[-1]['content'] + message['content'][0]['text']
                else:
                    new_msg_text = self.messages[-1]['content'][0]['text'] + message['content'][0]['text']
                self.messages.append({'role': message['role'], 'content': [{'type': 'text', 'text': new_msg_text}]})
        else:
            if len(self.messages)>0:
                print('roles do not repeat, last message role is ', self.messages[-1]['role'], 'new message role is ', message['role'])
            debug_box("5")
            self.messages.append(message)
        self.save_log()

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages

    def get_recent(self, max_tokens: int = 4096) -> List[Dict[str, str]]:
        recent_messages = []
        total_length = 0
        json_messages = json.dumps(self.messages)
        return json.loads(json_messages)

    def save_log(self) -> None:
        log_file = os.path.join(self.log_dir, f'chatlog_{self.log_id}.json')
        with open(log_file, 'w') as f:
            json.dump(self._get_log_data(), f, indent=2)
        # Invalidate cache when log is saved
        _invalidate_log_cache()
        

    def load_log(self, log_id = None) -> None:
        if log_id is None:
            log_id = self.log_id
        self.log_id = log_id
        log_file = os.path.join(self.log_dir, f'chatlog_{log_id}.json')
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                self.agent = log_data.get('agent')
                self.messages = log_data.get('messages', [])
                self.parent_log_id = log_data.get('parent_log_id', None)
            print("Loaded log file at ", log_file)
            print("Message length: ", len(self.messages))
        else:
            print("Could not find log file at ", log_file)
            self.messages = []

    def count_tokens(self) -> Dict[str, int]:
        input_tokens_sequence = 0
        output_tokens_sequence = 0
        input_tokens_total = 0
        
        for i, message in enumerate(self.messages):
            message_tokens = len(json.dumps(message)) // 4
            
            if message['role'] == 'assistant':
                output_tokens_sequence += message_tokens
            else:
                input_tokens_sequence += message_tokens
            
            if message['role'] == 'assistant':
                request_input_tokens = 0
                for j in range(i):
                    request_input_tokens += len(json.dumps(self.messages[j])) // 4
                input_tokens_total += request_input_tokens
        
        return {
            'input_tokens_sequence': input_tokens_sequence,
            'output_tokens_sequence': output_tokens_sequence,
            'input_tokens_total': input_tokens_total
        }

def _invalidate_log_cache():
    """Invalidate the log index cache"""
    global _log_index_cache
    with _log_index_cache['scan_lock']:
        _log_index_cache['last_scan'] = 0

def _build_log_index(force_refresh: bool = False) -> None:
    """
    Build an index of all chat logs and their relationships.
    This replaces the inefficient os.walk() calls with a single scan.
    """
    global _log_index_cache
    
    with _log_index_cache['scan_lock']:
        current_time = time.time()
        
        # Only rebuild if cache is older than 5 minutes or forced
        if not force_refresh and (current_time - _log_index_cache['last_scan']) < 300:
            return
        
        print("Building log index cache...")
        start_time = time.time()
        
        # Clear existing cache
        _log_index_cache['log_paths'].clear()
        _log_index_cache['parent_children'].clear()
        _log_index_cache['log_metadata'].clear()
        
        chat_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
        if not os.path.exists(chat_dir):
            _log_index_cache['last_scan'] = current_time
            return
        
        # Single directory walk to build complete index
        for root, dirs, files in os.walk(chat_dir):
            for file in files:
                if file.startswith("chatlog_") and file.endswith(".json"):
                    # Extract log_id from filename
                    log_id = file[8:-5]  # Remove 'chatlog_' prefix and '.json' suffix
                    full_path = os.path.join(root, file)
                    
                    try:
                        # Get file modification time
                        mtime = os.path.getmtime(full_path)
                        
                        # Parse user and agent from path
                        rel_path = os.path.relpath(full_path, chat_dir)
                        path_parts = rel_path.split(os.sep)
                        user = path_parts[0] if len(path_parts) > 0 else 'unknown'
                        agent = path_parts[1] if len(path_parts) > 1 else 'unknown'
                        
                        # Store path mapping
                        _log_index_cache['log_paths'][log_id] = full_path
                        
                        # Read log data to get parent relationship
                        try:
                            with open(full_path, 'r') as f:
                                log_data = json.load(f)
                                parent_log_id = log_data.get('parent_log_id')
                                
                                # Store metadata
                                _log_index_cache['log_metadata'][log_id] = {
                                    'parent_log_id': parent_log_id,
                                    'agent': agent,
                                    'user': user,
                                    'mtime': mtime
                                }
                                
                                # Build parent-child relationships
                                if parent_log_id:
                                    _log_index_cache['parent_children'][parent_log_id].add(log_id)
                                    
                        except (json.JSONDecodeError, KeyError) as e:
                            print(f"Error reading log file {full_path}: {e}")
                            continue
                            
                    except OSError as e:
                        print(f"Error accessing file {full_path}: {e}")
                        continue
        
        _log_index_cache['last_scan'] = current_time
        elapsed = time.time() - start_time
        print(f"Log index built in {elapsed:.2f}s. Found {len(_log_index_cache['log_paths'])} logs.")

def find_chatlog_file(log_id: str) -> Optional[str]:
    """
    Find a chatlog file by its log_id using the cached index.
    
    Args:
        log_id: The log ID to search for
        
    Returns:
        The full path to the chatlog file if found, None otherwise
    """
    _build_log_index()
    return _log_index_cache['log_paths'].get(log_id)

def find_child_logs_by_parent_id(parent_log_id: str) -> List[str]:
    """
    Find all chat logs that have the given parent_log_id using the cached index.
    
    Args:
        parent_log_id: The parent log ID to search for
        
    Returns:
        List of log IDs that have this parent_log_id
    """
    _build_log_index()
    return list(_log_index_cache['parent_children'].get(parent_log_id, set()))

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

def count_tokens_for_log_id_optimized(log_id: str) -> Dict[str, int]:
    """
    Optimized version of count_tokens_for_log_id that uses caching and batch operations.
    
    Args:
        log_id: The log ID to count tokens for
        
    Returns:
        Dictionary with token counts or None if log not found
    """
    # Find the chatlog file using cached index
    chatlog_path = find_chatlog_file(log_id)
    if not chatlog_path:
        return None
    
    # Check cache first
    cached_counts = get_cached_token_counts(log_id, chatlog_path)
    if cached_counts:
        print(f"Using cached token counts for {log_id}")
        return cached_counts
    
    print(f"Calculating token counts for {log_id}")
    
    # Use batch processing to get all related logs at once
    all_related_logs = _get_all_related_logs_batch(log_id)
    
    # Calculate tokens for all logs in batch
    token_results = {}
    for related_log_id, log_data in all_related_logs.items():
        # Create a temporary ChatLog instance to count tokens
        temp_log = ChatLog(log_id=related_log_id, user="system", agent=log_data.get('agent', 'unknown'))
        temp_log.messages = log_data.get('messages', [])
        
        # Count tokens for this log
        token_results[related_log_id] = temp_log.count_tokens()
    
    # Build the hierarchical token counts
    main_counts = token_results.get(log_id, {
        'input_tokens_sequence': 0,
        'output_tokens_sequence': 0,
        'input_tokens_total': 0
    })
    
    # Sum up all child tokens
    combined_counts = {
        'input_tokens_sequence': main_counts['input_tokens_sequence'],
        'output_tokens_sequence': main_counts['output_tokens_sequence'],
        'input_tokens_total': main_counts['input_tokens_total']
    }
    
    # Add child log tokens
    for related_log_id, counts in token_results.items():
        if related_log_id != log_id:  # Don't double-count the main log
            combined_counts['input_tokens_sequence'] += counts['input_tokens_sequence']
            combined_counts['output_tokens_sequence'] += counts['output_tokens_sequence']
            combined_counts['input_tokens_total'] += counts['input_tokens_total']
    
    # Create final result
    final_token_counts = {
        # Parent session only counts
        'input_tokens_sequence': main_counts['input_tokens_sequence'],
        'output_tokens_sequence': main_counts['output_tokens_sequence'],
        'input_tokens_total': main_counts['input_tokens_total'],
        # Combined counts (parent + all subtasks)
        'combined_input_tokens_sequence': combined_counts['input_tokens_sequence'],
        'combined_output_tokens_sequence': combined_counts['output_tokens_sequence'],
        'combined_input_tokens_total': combined_counts['input_tokens_total']
    }
    
    # Save to cache
    save_token_counts_to_cache(log_id, final_token_counts)
    
    return final_token_counts

def _get_all_related_logs_batch(log_id: str) -> Dict[str, Dict]:
    """
    Get all related logs (parent and children) in a single batch operation.
    This avoids multiple directory traversals and file reads.
    """
    # Ensure index is built
    _build_log_index()
    
    # Find all related log IDs
    related_log_ids = set([log_id])
    to_process = [log_id]
    
    while to_process:
        current_id = to_process.pop()
        
        # Add children
        children = _log_index_cache['parent_children'].get(current_id, set())
        for child_id in children:
            if child_id not in related_log_ids:
                related_log_ids.add(child_id)
                to_process.append(child_id)
    
    # Also check for delegated tasks in the main log
    main_log_path = _log_index_cache['log_paths'].get(log_id)
    if main_log_path:
        try:
            with open(main_log_path, 'r') as f:
                log_data = json.load(f)
                delegated_ids = extract_delegate_task_log_ids(log_data.get('messages', []))
                for delegated_id in delegated_ids:
                    if delegated_id not in related_log_ids:
                        related_log_ids.add(delegated_id)
                        to_process.append(delegated_id)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Batch read all related logs
    result = {}
    for related_id in related_log_ids:
        log_path = _log_index_cache['log_paths'].get(related_id)
        if log_path:
            try:
                with open(log_path, 'r') as f:
                    result[related_id] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading log {related_id}: {e}")
                continue
    
    return result

# Backward compatibility - keep the original function name but use optimized version
def count_tokens_for_log_id(log_id: str) -> Dict[str, int]:
    """
    Count tokens for a chat log identified by log_id, including any delegated tasks.
    This is the optimized version that uses caching and batch operations.
    """
    return count_tokens_for_log_id_optimized(log_id)
