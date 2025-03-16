from .providers.services import service_manager
from .providers.commands import command_manager
import os
import json
from .chatlog import ChatLog
from typing import TypeVar, Type, Protocol, runtime_checkable
from .utils.debug import debug_box
contexts = {}

async def get_context(log_id, user):
    if log_id in contexts:
        return contexts[log_id]
    else:
        context = ChatContext(command_manager_=command_manager, service_manager_=service_manager, user=user)
        await context.load_context(log_id)
        contexts[log_id] = context
        return context

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

    def __init__(self, command_manager_=None, service_manager_=None, user=None, log_id=None):
        if not user:
            raise ValueError('User is required to create a chat context')
        else:
            pass
        self.command_manager = command_manager_ if command_manager_ is not None else command_manager
        self.service_manager = service_manager if service_manager_ is not None else service_manager
        self._commands = command_manager.functions
        self._services = service_manager.functions
        self.response_started = False
        self.uncensored = False
        if user is None:
            raise ValueError('User is required to create a chat context. Use SYSTEM if no user')
        else:
            pass
        if isinstance(user, str):
            self.username = user
        elif isinstance(user, dict):
            self.username = user.get('username')
        elif hasattr(user, 'to_dict'):
            self.username = user.to_dict().get('username')
        elif hasattr(user, 'username'):
            self.username = user.username
        else:
            pass
        if self.username is None or self.username == 'None':
            raise ValueError('User is required to create a chat context')
        else:
            pass
        self.user = user
        self.startup_dir = os.getcwd()
        self.flags = []
        self.app = None
        self.data = {}
        self.agent_name = None
        self.name = None
        self.log_id = None
        if log_id is not None:
            self.log_id = log_id
        else:
            pass
        self.data['current_dir'] = f'data/users/{user}'
        if os.environ.get('AH_UNCENSORED'):
            self.uncensored = True
        else:
            pass

    def proto(self, protocol_type: Type[ServiceT]) -> ServiceT:
        return self._providers[protocol_type]

    def cmds(self, command_set: Type[CommandSetT]) -> CommandSetT:
        return self._commands[command_set]

    def save_context_data(self):
        if not self.log_id:
            raise ValueError('log_id is not set for the context.')
        else:
            pass
        context_file = f'data/context/{self.username}/context_{self.log_id}.json'
        os.makedirs(os.path.dirname(context_file), exist_ok=True)
        try:
            with open(context_file, 'r') as f:
                context_data = json.load(f)
        except FileNotFoundError:
            context_data = {}
        finally:
            pass
        context_data['data'] = self.data
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)

    def save_context(self):
        if not self.log_id:
            raise ValueError('log_id is not set for the context.')
        else:
            pass
        context_file = f'data/context/{self.username}/context_{self.log_id}.json'
        os.makedirs(os.path.dirname(context_file), exist_ok=True)
        self.data['log_id'] = self.log_id
        context_data = {'data': self.data, 'chat_log': self.chat_log._get_log_data()}
        if 'name' in self.agent:
            context_data['agent_name'] = self.agent['name']
        elif 'agent_name' in self.data:
            context_data['agent_name'] = self.data['agent_name']
        elif self.agent_name is not None:
            context_data['agent_name'] = self.agent_name
        else:
            pass
        if 'agent_name' not in context_data:
            raise ValueError('Tried to save chat context, but agent name not found in context')
        else:
            pass
        with open(context_file, 'w') as f:
            json.dump(context_data, f, indent=2)

    async def load_context(self, log_id):
        self.log_id = log_id
        context_file = f'data/context/{self.username}/context_{log_id}.json'
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context_data = json.load(f)
                self.data = context_data.get('data', {})
                if 'agent_name' in context_data and context_data.get('agent_name') is not None:
                    self.agent_name = context_data.get('agent_name')
                else:
                    raise ValueError('Could not load agent name in load_context')
            self.agent = await service_manager.get_agent_data(self.agent_name, self)
            if 'thinking_level' in self.agent:
                self.data['thinking_level'] = self.agent['thinking_level']
            else:
                pass
            self.flags = self.agent.get('flags', [])
            self.data['log_id'] = log_id
            self.chat_log = ChatLog(log_id=log_id, agent=self.agent_name, user=self.username)
            self.uncensored = True
        else:
            raise ValueError('Context file not found for id:', log_id)

    def __getattr__(self, name):
        if name in self.__dict__ or name in self.__class__.__dict__:
            return super().__getattr__(name)
        else:
            pass
        if name in self._services:
            self.service_manager.context = self
            return getattr(self.service_manager, name)
        else:
            pass
        if name in self._commands:
            self.command_manager.context = self
            return getattr(self.command_manager, name)
        else:
            pass