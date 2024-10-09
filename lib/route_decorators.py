from fastapi import FastAPI, Request
from typing import Set
from functools import wraps

app = FastAPI()
public_routes: Set[str] = set()

def public_route():
    # include route path/function name
    print("public_route decorator called", public_routes)
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            print("public route !!!!!!!!!!!")
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.public_route = True
            return await func(*args, **kwargs)
        wrapper.__public_route__ = True
        public_routes.add(func.__name__)
        print("wrapper.__public_route__", wrapper.__public_route__)
        return wrapper
    return decorator


