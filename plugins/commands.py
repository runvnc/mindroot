class CommandManager:
    def __init__(self):
        self.commands = {}

    def register_command(self, name, implementation, docstring):
        if name in self.commands:
            raise ValueError(f"Command '{name}' is already registered.")
        self.commands[name] = (implementation, docstring)

    def execute(self, name, *args, **kwargs):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        implementation, _ = self.commands[name]
        return implementation(*args, **kwargs)

    def get_docstring(self, name):
        if name not in self.commands:
            raise ValueError(f"Command '{name}' not found.")
        _, docstring = self.commands[name]
        return docstring

# Singleton pattern for easy access globally
command_manager = CommandManager()

def command(name):
    def decorator(func):
        docstring = func.__doc__
        command_manager.register_command(name, func, docstring)
        return func
    return decorator

