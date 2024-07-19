from fastapi import FastAPI, Request
from typing import Set

app = FastAPI()
public_routes: Set[str] = set()

def public_route():
    def decorator(func):
        path = None

        async def wrapper(*args, **kwargs):
            nonlocal path
            if path:
                request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
                if request:
                    print(f'Setting public_route to True for {request.url.path}')
                    request.state.public_route = True
            return await func(*args, **kwargs)

        async def wrapped_func(*args, **kwargs):
            return await func(*args, **kwargs)

        path = func.__route_path__
        public_routes.add(path)
        return wraps(func)(wrapped_func)
    return decorator


