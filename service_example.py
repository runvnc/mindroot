import json
import importlib

class ServiceContext:
    def __init__(self):
        self._services = {}

    def register_service(self, name, func):
        self._services[name] = func

    def __getattr__(self, name):
        if name in self._services:
            return self._services[name]
        raise AttributeError(f"'ServiceContext' object has no attribute '{name}'")

context = ServiceContext()

def service(name):
    def decorator(func):
        context.register_service(name, func)
        return func
    return decorator

# Load active service from config
with open('config.json') as config_file:
    config = json.load(config_file)
    active_service = config['active_service']
    importlib.import_module(f'plugins.{active_service}')

# Example usage
if __name__ == "__main__":
    print(context.my_service_func("hello", 10))  # Output will depend on the active service
