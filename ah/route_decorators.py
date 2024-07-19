from functools import wraps
from fastapi import Request

def public_route():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                print(f'Setting public_route to True for {request.url.path}')
                request.state.public_route = True
            return await func(*args, **kwargs)
        wrapper.__public_route__ = True
        return wrapper
    return decorator


