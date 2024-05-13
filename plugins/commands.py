class CommandManager:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, implementation, docstring, is_local=False):
    def register_command(self, name, implementation, docstring):
        if name in self.commands:
            raise ValueError(f"Command '{name}' is already registered.")
        self.commands[name] = {
            'implementation': implementation,
            'docstring': docstring,
            'is_local': is_local
        }

    def execute(self, name, *args, **kwargs):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        command_info = self.commands[name]
        implementation = command_info['implementation']
        return implementation(*args, **kwargs)

    def get_docstring(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        docstring = self.commands[name]['docstring']
        return docstring

    def is_local_command(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        return self.commands[name]['is_local']

# Singleton pattern for easy access globally
command_manager = CommandManager()

def command(name, *, is_local=False):
    def decorator(func):
        docstring = func.__doc__
        command_manager.register_command(name, func, docstring, is_local)
        return func
    return decorator

