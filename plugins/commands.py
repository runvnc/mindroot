class CommandManager:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, implementation, docstring, is_local=False):
    def register_command(self, name, implementation, docstring):
        if name in self.commands:
            raise ValueError(f"Command '{name}' is already registered.")
        if name in self.commands and is_local in self.commands[name]:
            raise ValueError(f"Command '{name}' with is_local={is_local} is already registered.")
        if name not in self.commands:
            self.commands[name] = {}
        self.commands[name][is_local] = {
            'implementation': implementation,
            'docstring': docstring,
            'is_local': is_local
        }

    def execute(self, name, prefer_local=False, *args, **kwargs):
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
        return implementation(*args, **kwargs)

    def get_docstring(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        # Prefer global command docstring if available
        docstring = self.commands[name].get(False, {}).get('docstring') or \
                    self.commands[name].get(True, {}).get('docstring')
        return docstring

    def is_local_command(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        # Check if a local version of the command exists
        return True in self.commands[name]

# Singleton pattern for easy access globally
command_manager = CommandManager()

def command(name, *, is_local=False):
    def decorator(func):
        docstring = func.__doc__
        command_manager.register_command(name, func, docstring, is_local)
        return func
    return decorator

