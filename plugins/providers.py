import inspect

class ProviderManager:
    def __init__(self):
        self.functions = {}

    def register_function(self, name, implementation, signature, docstring, is_local=False):
        if name in self.functions:
            print(f"function '{name}' is already registered.")
            #raise ValueError(f"function '{name}' is already registered.")
        if name in self.functions and is_local in self.functions[name]:
            print(f"function '{name}' with is_local={is_local} is already registered.")
            #raise ValueError(f"function '{name}' with is_local={is_local} is already registered.")
        if name not in self.functions:
            self.functions[name] = {}
            print('registering:', name, signature)

        self.functions[name][is_local] = {
            'implementation': implementation,
            'docstring': docstring,
            'is_local': is_local
        }
        print("registered function: ", name, is_local, implementation, docstring)

    async def execute(self, name, *args, **kwargs):
        print(f"execute! name= {name}, args={args}, kwargs={kwargs}")
        prefer_local = True
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        local_function_info = self.functions[name].get(True)
        global_function_info = self.functions[name].get(False)
        function_info = None
        if prefer_local and local_function_info:
            function_info = local_function_info
        elif global_function_info:
            function_info = global_function_info
        else:
            function_info = local_function_info  # Fallback to local if global is not available

        implementation = function_info['implementation']
        return await implementation(*args, **kwargs)

    def get_docstring(self, name, prefer_local=False):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")

        docstring = None
        if prefer_local:
            docstring = self.functions[name][True]['docstring']
        if not docstring:
            docstring = self.functions[name][False]['docstring']
        return docstring

    def get_functions(self):
        return list(self.functions.keys())

    def get_docstrings(self, prefer_local=True):
        return [self.get_docstring(name, prefer_local=prefer_local) for name in self.functions.keys()]

    def get_some_docstrings(self, names, prefer_local=False):
        return {name: self.get_docstring(name, prefer_local=prefer_local) for name in names}

    def is_local_function(self, name):
        if name not in self.functions:
            raise ValueError(f"function '{name}' not found.")
        # Check if a local version of the function exists
        return True in self.functions[name]

    def __getattr__(self, name):
        #if name in self.__dict__ or name in self.__class__.__dict__:
        #    return super().__getattr__(name)
        
        def method(*args, **kwargs):
            print(f'Called method: {name}')
            print(f'Arguments: {args}')
            print(f'Keyword arguments: {kwargs}')
            self.execute(name, *args, **kwargs)

        return method

    def handle_specific_method(self, *args, **kwargs):
        # Specific method handler
        return "Handled specific_method"


