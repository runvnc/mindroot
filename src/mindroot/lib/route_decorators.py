from fastapi import FastAPI, Request, Depends, HTTPException
from typing import Set, List
from functools import wraps

app = FastAPI()

# Preserve existing public routes functionality
public_routes: Set[str] = set()
public_static: Set[str] = set()

def public_route():
    """Decorator to mark a route as public (no authentication required)"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Mark the request as a public route for any middleware that needs to know
            request: Request = next((arg for arg in args if isinstance(arg, Request)), None)
            if request:
                request.state.public_route = True
            return await func(*args, **kwargs)
        
        # Mark the function as a public route so the startup hook can find it
        wrapper.__public_route__ = True
        return wrapper
    return decorator

def add_public_static(path_start):
    """Add a path prefix to the public static routes"""
    public_static.add(path_start)

# New role-based dependency functions
def requires_role(role: str):
    return requires_any_role(role)

def requires_any_role(*roles: str):
    def role_checker(request: Request):
        if not request.state.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_roles = request.state.user.roles
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=403,
                detail=f"User needs one of these roles: {', '.join(roles)}"
            )
        return True
    return Depends(role_checker)

def requires_all_roles(*roles: str):
    def role_checker(request: Request):
        if not request.state.user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user_roles = request.state.user.roles
        missing_roles = [role for role in roles if role not in user_roles]
        if missing_roles:
            raise HTTPException(
                status_code=403,
                detail=f"User lacks required roles: {', '.join(missing_roles)}"
            )
        return True
    return Depends(role_checker)
