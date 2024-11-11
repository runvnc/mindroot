import inspect
from typing import Any, Callable
from .pipelines import PipelineManager

pipeline_manager = PipelineManager()

def pipe(name: str, priority: int = 0):
    def decorator(func: Callable[[Any], Any]):
        #print message in cyan that we are registering
        print(f"\033[96mRegistering pipe: {name}\033[0m")
        docstring = func.__doc__
        signature = inspect.signature(func)
        pipeline_manager.register_pipe(name, func, signature, docstring, priority)
        return func
    return decorator
