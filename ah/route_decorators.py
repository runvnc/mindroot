from fastapi import FastAPI, Request
from typing import Set
from functools import wraps

app = FastAPI()
public_routes: Set[str] = set()

def public_route():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.public_route = True
            return await func(*args, **kwargs)
        wrapper.__public_route__ = True
        return wrapper
    return decorator


