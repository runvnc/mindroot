import inspect
from typing import Any, Callable, Dict, List
import asyncio

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
        # Sort pipes by priority
        self.pipes[name].sort(key=lambda x: x['priority'])

    async def execute_pipeline(self, name: str, data: Any) -> Any:
        if name not in self.pipes:
            return data
        for pipe_info in self.pipes[name]:
            implementation = pipe_info['implementation']
            try:
                if asyncio.iscoroutinefunction(implementation):
                    data = await implementation(data)
                else:
                    data = implementation(data)
            except Exception as e:
                print(f"Error in pipeline '{name}' at step with priority {pipe_info['priority']}: {str(e)}")
                # Optionally, you could raise the exception here if you want to halt the pipeline on errors
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

pipeline_manager = PipelineManager()
