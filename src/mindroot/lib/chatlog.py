import os
import json
from typing import List, Dict
import sys
import traceback

class ChatLog:
    def __init__(self, log_id=0, agent=None, context_length: int = 4096):
        self.log_id = log_id
        self.messages = []
        self.agent = agent
        if agent is None or agent == '':
            raise ValueError('Agent must be provided')
        self.context_length = context_length
        self.log_dir = os.environ.get('CHATLOG_DIR', 'data/chat')
        self.log_dir = os.path.join(self.log_dir, self.agent)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.load_log()

    def _get_log_data(self) -> Dict[str, any]:
        return {
            'agent': self.agent,
            'messages': self.messages
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
                    cmd_list = [cmd_list]
                new_json = json.loads(message['content'][0]['text'])
                if type(new_json) != list:
                    new_json = [new_json]
                new_cmd_list = cmd_list + new_json
                self.messages[-1]['content'] = [{ 'type': 'text', 'text': json.dumps(new_cmd_list) }]
            except Exception as e:
                # assume previous mesage was not a command, was a string
                new_msg_text = self.messages[-1]['content'][0]['text'] + message['content'][0]['text']
                self.messages.append({'role': message['role'], 'content': [{'type': 'text', 'text': new_msg_text}]})
                #print('could not combine commands. probably normal if user message and previous system output', e)
                #print(self.messages[-1])
                #print(message)
                #raise e
        else:
            if len(self.messages)>0:
                print('roles do not repeat, last message role is ', self.messages[-1]['role'], 'new message role is ', message['role'])
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
        # change to blinking text with ANSI attributes
        print('\033[5m\033[1m\033[31m')
        print('saved log')
        traceback.print_stack()
        print('\033[0m')
        

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
        else:
            self.messages = []
