from .providers.services import service_manager
from .providers.commands import command_manager
import os
import json
from .chatlog import ChatLog
from typing import TypeVar, Type, Protocol, runtime_checkable

@runtime_checkable
class BaseService(Protocol):
    """Base protocol for all services"""
    pass

class BaseCommandSet(Protocol):
    """Base protocol for all command sets"""
    pass

ServiceT = TypeVar('ServiceT', bound=BaseService)
CommandSetT = TypeVar('CommandSetT', bound=BaseCommandSet)

class ChatContext:

    def __init__(self, command_manager, service_manager, user='testuser'):
        self.command_manager = command_manager
        self.service_manager = service_manager
        self._commands = command_manager.functions
        self._services = service_manager.functions
        self.response_started = False
        self.uncensored = False
        self.flags = []

        self.data = {}
        self.agent_name = None
        self.name = None
        self.log_id = None
        self.data['current_dir'] = f'data/users/{user}'
        if os.environ.get("AH_UNCENSORED"):
            self.uncensored = True

    def proto(self, protocol_type: Type[ServiceT]) -> ServiceT:
        return self._providers[protocol_type]

    def cmds(self, command_set: Type[CommandSetT]) -> CommandSetT:
        return self._commands[command_set]

    def save_context(self):
        if not self.log_id:
            raise ValueError("log_id is not set for the context.")
        context_file = f'data/context/context_{self.log_id}.json'
        self.data['log_id'] = self.log_id
        context_data = {
            'data': self.data,
            'chat_log': self.chat_log._get_log_data(),
        }
        if 'name' in self.agent:
            context_data['agent_name'] = self.agent['name']
        elif 'agent_name' in self.data:
            context_data['agent_name'] = self.data['agent_name']
        elif self.agent_name is not None:
            context_data['agent_name'] = self.agent_name
        if 'agent_name' not in context_data:
            raise ValueError("Tried to save chat context, but agent name not found in context")
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)
        print("Saved context to:", context_file)

    async def load_context(self, log_id):
        self.log_id = log_id
        context_file = f'data/context/context_{log_id}.json'
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context_data = json.load(f)
                self.data = context_data.get('data', {})
                print(self.data)
                print(context_data)
                if 'agent_name' in context_data and context_data.get('agent_name') is not None:
                    self.agent_name = context_data.get('agent_name')
                else:
                    raise ValueError("Could not load agent name in load_context")
                print('agent_name=', self.agent_name)
                print('context_data', context_data)
            self.agent = await service_manager.get_agent_data(self.agent_name, self)
            self.flags = self.agent.get('flags', [])
            self.data['log_id'] = log_id
            self.chat_log = ChatLog(log_id=log_id, agent=self.agent_name)

            self.uncensored = True
        else:
            print("Context file not found for id:", log_id)
            raise ValueError("Context file not found for id:", log_id)

    def __getattr__(self, name):
        if name in self.__dict__ or name in self.__class__.__dict__:
            return super().__getattr__(name)

        if name in self._services:
            self.service_manager.context = self
            return getattr(self.service_manager, name)

        if name in self._commands:
            self.command_manager.context = self
            return getattr(self.command_manager, name)


