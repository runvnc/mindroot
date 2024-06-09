from .services import service_manager
from .commands import command_manager
import os
import json
from .chatlog import ChatLog

class ChatContext:
    def __init__(self, command_manager, service_manager):
        self.command_manager = command_manager
        self.service_manager = service_manager
        self._commands = command_manager.functions
        self._services = service_manager.functions
        self.response_started = False
        self.uncensored = False
        self.flags = []

        self.data = {}
        self.log_id = None
        self.data['current_dir'] = 'data/users/default'

        if os.environ.get("AH_UNCENSORED"):
            self.uncensored = True

    def save_context(self):
        if not self.log_id:
            raise ValueError("log_id is not set for the context.")
        context_file = f'data/context/context_{self.log_id}.json'
        context_data = {
            'data': self.data,
            'chat_log': self.chat_log._get_log_data(),
        }
        if 'name' in self.agent:
            context_data['agent_name'] = self.agent['name']
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)        

    async def load_context(self, log_id):
        self.log_id = log_id
        context_file = f'data/context/context_{log_id}.json'
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context_data = json.load(f)
                self.data = context_data.get('data', {})
                self.chat_log = ChatLog(log_id=log_id)
            self.agent_name = context_data.get('agent_name')  
            self.agent = await service_manager.get_agent_data(self.agent_name, self)
            self.flags = self.agent.get('flags', [])
            self.chat_log = ChatLog(log_id=log_id)
            self.uncensored = True
        else:
            print("Context file not found for id:", log_id)

    def __getattr__(self, name):
        if name in self.__dict__ or name in self.__class__.__dict__:
            return super().__getattr__(name)

        if name in self._services:
            self.service_manager.context = self
            return getattr(self.service_manager, name)

        if name in self._commands:
            self.command_manager.context = self
            return getattr(self.command_manager, name)


