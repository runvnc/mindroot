import os
import json
from typing import List, Dict

class ChatLog:
    def __init__(self, log_id=0, persona=None, context_length: int = 4096):
        self.log_id = 0
        self.messages = []
        self.persona = persona
        self.context_length = context_length
        self.log_dir = os.environ.get('CHATLOG_DIR', 'data/chat')

    def _calculate_message_length(self, message: Dict[str, str]) -> int:
        return len(json.dumps(message)) // 3

    def add_message(self, message: Dict[str, str]) -> None:
        self.messages.append(message)
        self._save_log()

    def get_history(self) -> List[Dict[str, str]]:
        return self.messages

    def get_recent(self, max_tokens: int = 4096) -> List[Dict[str, str]]:
        recent_messages = []
        total_length = 0
        print('returning all messages', self.messages)
        return self.messages

        #for message in self.messages:
        #    message_length = self._calculate_message_length(message)
        #    if total_length + message_length <= max_tokens:
        #        recent_messages.append(message)
        #        total_length += message_length
        #    else:
        #        break
        # 
        #return recent_messages

    def _save_log(self) -> None:
        log_file = os.path.join(self.log_dir, f'chatlog_{self.log_id}.json')
        with open(log_file, 'w') as f:
            json.dump(self.messages, f, indent=2)

    def load_log(self, log_id: int) -> None:
        self.log_id = log_id
        log_file = os.path.join(self.log_dir, f'chatlog_{log_id}.json')
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                self.messages = json.load(f)
        else:
            self.messages = []
