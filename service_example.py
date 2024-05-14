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

# Define a service function
@service('my_service_func')
def my_service_func(param1, param2):
    return f"Service called with {param1} and {param2}"

# Swap out the service function
@service('my_service_func')
def my_new_service_func(param1, param2):
    return f"New service called with {param1} and {param2}"

# Example usage
if __name__ == "__main__":
    print(context.my_service_func("hello", 10))  # Output: New service called with hello and 10
