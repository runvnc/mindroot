import inspect
from typing import Any, Callable, Dict, List
import asyncio
import termcolor

class PipelineManager:
    def __init__(self):
        self.pipes: Dict[str, List[Dict[str, Any]]] = {}

    def register_pipe(self, name: str, implementation: Callable, signature: inspect.Signature, docstring: str, priority: int):
        if name not in self.pipes:
            self.pipes[name] = []
        self.pipes[name].append({
            'implementation': implementation,
            'docstring': docstring,
            'priority': priority,
            'signature': signature
        })
        print(termcolor.colored(f"Registering pipe '{name}' with priority {priority}", 'yellow'))
        self.pipes[name].sort(key=lambda x: x['priority'])

    async def execute_pipeline(self, name: str, data: Any, context=None) -> Any:
        # print debug in yellow
        # print all debugs in yellow
        print(termcolor.colored(f"Executing pipeline '{name}'", 'yellow'))
        if name not in self.pipes:
            print(termcolor.colored(f"Pipeline '{name}' not found", 'red'))
            return data
        print(termcolor.colored(f"Pipeline '{name}' found", 'yellow'))
        print(self.pipes[name])
        for pipe_info in self.pipes[name]:
            implementation = pipe_info['implementation']
            print(termcolor.colored(f"Executing step with priority {pipe_info['priority']}", 'yellow'))
            try:
                if asyncio.iscoroutinefunction(implementation):
                    data = await implementation(data, context)
                else:
                    data = implementation(data, context)
            except Exception as e:
                #print in red
                print(termcolor.colored(f"Error in pipeline '{name}' at step with priority {pipe_info['priority']}: {str(e)}", 'red'))
                # raise e
        return data

    def get_registered_pipes(self) -> Dict[str, List[Dict[str, Any]]]:
        return {name: [{'priority': p['priority'], 'docstring': p['docstring']} for p in pipes]
                for name, pipes in self.pipes.items()}

    def clear_pipeline(self, name: str) -> None:
        if name in self.pipes:
            del self.pipes[name]

    def remove_pipe(self, name: str, priority: int) -> bool:
        if name in self.pipes:
            self.pipes[name] = [p for p in self.pipes[name] if p['priority'] != priority]
            return True
        return False

    def __getattr__(self, name: str) -> Callable:
        async def pipeline_method(*args, **kwargs):
            return await self.execute_pipeline(name, *args, **kwargs)
        return pipeline_method

