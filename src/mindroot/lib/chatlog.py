import os
import json
from typing import List, Dict
import sys
import traceback
import re
import time
from mindroot.lib.utils.debug import debug_box

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
                #print('could not combine commands. probably normal if user message and previous system output', e)
                #print(self.messages[-1])
                #print(message)
                #raise e
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
        #print('returning all messages', self.messages)
        json_messages = json.dumps(self.messages)
        return json.loads(json_messages)

        #for message in self.messages:
        #    message_length = self._calculate_message_length(message)
        #    if total_length + message_length <= max_tokens:
        #        recent_messages.append(message)
        #        total_length += message_length
        #    else:
        #        break
        # 
        #return recent_messages

    def save_log(self) -> None:
        log_file = os.path.join(self.log_dir, f'chatlog_{self.log_id}.json')
        with open(log_file, 'w') as f:
            json.dump(self._get_log_data(), f, indent=2)
        

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
        """
        Count tokens in the chat log, providing both sequence totals and cumulative request totals.
        
        Returns:
            Dict with the following keys:
            - input_tokens_sequence: Total tokens in all user messages
            - output_tokens_sequence: Total tokens in all assistant messages
            - input_tokens_total: Cumulative tokens sent to LLM across all requests
        """
        # Initialize counters
        input_tokens_sequence = 0  # Total tokens in all user messages
        output_tokens_sequence = 0  # Total tokens in all assistant messages
        input_tokens_total = 0  # Cumulative tokens sent to LLM across all requests
        
        # Process each message
        for i, message in enumerate(self.messages):
            # Calculate tokens in this message (rough approximation)
            message_tokens = len(json.dumps(message)) // 4
            
            # Add to appropriate sequence counter
            if message['role'] == 'assistant':
                output_tokens_sequence += message_tokens
            else:  # user or system
                input_tokens_sequence += message_tokens
            
            # For each assistant message, calculate the input tokens for that request
            # (which includes all previous messages)
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

def find_child_logs_by_parent_id(parent_log_id: str) -> List[str]:
    """
    Find all chat logs that have the given parent_log_id.
    
    Args:
        parent_log_id: The parent log ID to search for
        
    Returns:
        List of log IDs that have this parent_log_id
    """
    child_log_ids = []
    chat_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
    
    # Search through all chatlog files
    for root, dirs, files in os.walk(chat_dir):
        for file in files:
            if file.startswith("chatlog_") and file.endswith(".json"):
                try:
                    with open(os.path.join(root, file), 'r') as f:
                        log_data = json.load(f)
                        if log_data.get('parent_log_id') == parent_log_id:
                            # Extract log_id from the data
                            child_log_ids.append(log_data.get('log_id'))
                except (json.JSONDecodeError, IOError):
                    continue
    
    return child_log_ids

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
    
    # Get parent_log_id if it exists
    parent_log_id = log_data.get('parent_log_id')
        
    # Create a temporary ChatLog instance to count tokens
    temp_log = ChatLog(log_id=log_id, user="system", agent=log_data.get('agent', 'unknown'))
    temp_log.messages = log_data.get('messages', [])
    
    # Count tokens for this log
    parent_counts = temp_log.count_tokens()
    
    # Create combined counts (starting with parent counts)
    combined_counts = {
        'input_tokens_sequence': parent_counts['input_tokens_sequence'],
        'output_tokens_sequence': parent_counts['output_tokens_sequence'],
        'input_tokens_total': parent_counts['input_tokens_total']
    }
    
    # Find delegated task log IDs
    delegated_log_ids = extract_delegate_task_log_ids(temp_log.messages)
    
    # Also find child logs by parent_log_id
    child_logs_by_parent = find_child_logs_by_parent_id(log_id)
    
    # Combine all child log IDs (delegated tasks and parent_log_id children)
    all_child_log_ids = set(delegated_log_ids) | set(child_logs_by_parent)
    
    # If this log has a parent_log_id, we should not double-count it
    # (it will be counted as part of its parent's cumulative total)
    # But we still want to count its own children
    
    # Recursively count tokens for all child tasks
    for child_id in all_child_log_ids:
        delegated_counts = count_tokens_for_log_id(child_id)
        if delegated_counts:
            combined_counts['input_tokens_sequence'] += delegated_counts['input_tokens_sequence']
            combined_counts['output_tokens_sequence'] += delegated_counts['output_tokens_sequence']
            combined_counts['input_tokens_total'] += delegated_counts['input_tokens_total']
    
    # Create final result with both parent and combined counts
    token_counts = {
        # Parent session only counts
        'input_tokens_sequence': parent_counts['input_tokens_sequence'],
        'output_tokens_sequence': parent_counts['output_tokens_sequence'],
        'input_tokens_total': parent_counts['input_tokens_total'],
        # Combined counts (parent + all subtasks)
        'combined_input_tokens_sequence': combined_counts['input_tokens_sequence'],
        'combined_output_tokens_sequence': combined_counts['output_tokens_sequence'],
        'combined_input_tokens_total': combined_counts['input_tokens_total']
    }
    
    # Save to cache
    save_token_counts_to_cache(log_id, token_counts)
    
    return token_counts
