from fastapi import FastAPI, Request
from typing import Set, Dict, List
from functools import wraps

app = FastAPI()

public_routes: Set[str] = set()
public_static: Set[str] = set()

class RouteRoleRequirement:
    def __init__(self, roles: List[str], require_all: bool):
        self.roles = roles
        self.require_all = require_all

protected_routes: Dict[str, RouteRoleRequirement] = {}

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

def add_public_static(path_start):
    public_static.add(path_start)

def requires_role(role: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.required_roles = [role]
                request.state.require_all = False
            
            print(f"requires_role {role} for {func.__name__}")
            return await func(*args, **kwargs)
            
        protected_routes[func.__name__] = RouteRoleRequirement([role], False)
        return wrapper
    return decorator

def requires_any_role(*roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.required_roles = roles
                request.state.require_all = False
            
            print(f"requires_any_role {roles} for {func.__name__}")
            return await func(*args, **kwargs)
            
        protected_routes[func.__name__] = RouteRoleRequirement(list(roles), False)
        return wrapper
    return decorator

def requires_all_roles(*roles: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.required_roles = roles
                request.state.require_all = True
            
            print(f"requires_all_roles {roles} for {func.__name__}")
            return await func(*args, **kwargs)
            
        protected_routes[func.__name__] = RouteRoleRequirement(list(roles), True)
        return wrapper
    return decorator
