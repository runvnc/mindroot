from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from lib.route_decorators import protected_routes

def check_route_roles(request: Request, route_name: str) -> bool:
    """Check if the user has the required roles for a route.
    Returns True if:
    - Route is not protected
    - User has the required role(s)
    Raises HTTPException if user lacks required roles.
    """
    # If route isn't protected, allow access
    if route_name not in protected_routes:
        return True
        
    requirement = protected_routes[route_name]
    
    # Get user's roles from state (set by middleware)
    user = getattr(request.state, 'user', None)
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    user_roles = user.get('roles', [])
    
    if requirement.require_all:
        # Check if user has ALL required roles
        if not all(role in user_roles for role in requirement.roles):
            missing_roles = [role for role in requirement.roles if role not in user_roles]
            raise HTTPException(
                status_code=403,
                detail=f"User lacks required roles: {', '.join(missing_roles)}"
            )
    else:
        # Check if user has ANY of the required roles
        if not any(role in user_roles for role in requirement.roles):
            raise HTTPException(
                status_code=403,
                detail=f"User needs one of these roles: {', '.join(requirement.roles)}"
            )
    
    return True
