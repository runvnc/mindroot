import inspect

class CommandManager:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, implementation, args, docstring, is_local=False):
        if name in self.commands:
            print(f"Command '{name}' is already registered.")
            #raise ValueError(f"Command '{name}' is already registered.")
        if name in self.commands and is_local in self.commands[name]:
            print(f"Command '{name}' with is_local={is_local} is already registered.")
            #raise ValueError(f"Command '{name}' with is_local={is_local} is already registered.")
        if name not in self.commands:
            self.commands[name] = {}

        self.commands[name][is_local] = {
            'implementation': implementation,
            'docstring': docstring,
            'is_local': is_local
        }
        print("registered command: ", name, is_local, implementation, docstring)

    async def execute(self, name, *args, **kwargs):
        print(f"execute! name= {name}, args={args}, kwargs={kwargs}")
        prefer_local = True
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        local_command_info = self.commands[name].get(True)
        global_command_info = self.commands[name].get(False)
        command_info = None
        if prefer_local and local_command_info:
            command_info = local_command_info
        elif global_command_info:
            command_info = global_command_info
        else:
            command_info = local_command_info  # Fallback to local if global is not available

        implementation = command_info['implementation']
        return await implementation(*args, **kwargs)

    def get_docstring(self, name, prefer_local=False):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")

        docstring = None
        if prefer_local:
            docstring = self.commands[name][True]['docstring']
        if not docstring:
            docstring = self.commands[name][False]['docstring']
        return docstring

    def get_commands(self):
        return list(self.commands.keys())

    def get_docstrings(self, prefer_local=True):
        return [self.get_docstring(name, prefer_local=prefer_local) for name in self.commands.keys()]

    def get_some_docstrings(self, names, prefer_local=False):
        return {name: self.get_docstring(name, prefer_local=prefer_local) for name in names}

    def is_local_command(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        # Check if a local version of the command exists
        return True in self.commands[name]

# Singleton pattern for easy access globally
command_manager = CommandManager()

def command(*, is_local=False):
    def decorator(func):
        docstring = func.__doc__
        name = func.__name__
        signature = inspect.signature(func)
        args = [param.name for param in signature.parameters.values()]
        command_manager.register_command(name, func, args, docstring, is_local)
        return func
    return decorator

