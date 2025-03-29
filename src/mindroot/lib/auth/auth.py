from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from typing import Optional, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[Any]:
    """
    Get the current authenticated user from the request state.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        The user object if authenticated, None otherwise
    """
    if hasattr(request.state, "user"):
        return request.state.user
    return None


async def require_user(request: Request, redirect_to_login: bool = False) -> Any:
    """
    Dependency to require an authenticated user for a route.
    
    Args:
        request: The FastAPI request object
        redirect_to_login: If True, redirects to /login when not authenticated
                         If False, raises an HTTPException with 401 status
    
    Returns:
        The user object if authenticated
        
    Raises:
        HTTPException: If the user is not authenticated (when redirect_to_login is False)
        RedirectResponse: If the user is not authenticated (when redirect_to_login is True)
    """
    user = await get_current_user(request)
    
    if user is None:
        logger.warning(f"Unauthorized access attempt to {request.url.path}")
        
        if redirect_to_login:
            return RedirectResponse(
                url=f"/login?next={request.url.path}",
                status_code=302
            )
        else:
            raise HTTPException(
                status_code=401, 
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    return user


async def require_admin(request: Request, redirect_to_login: bool = False) -> Any:
    """
    Dependency to require an authenticated admin user for a route.
    
    Args:
        request: The FastAPI request object
        redirect_to_login: If True, redirects to /login when not authenticated
                         If False, raises an HTTPException with 401/403 status
    
    Returns:
        The user object if authenticated and has admin role
        
    Raises:
        HTTPException: If the user is not authenticated or lacks admin privileges
        RedirectResponse: If the user is not authenticated (when redirect_to_login is True)
    """
    user = await require_user(request, redirect_to_login)
    
    # Check if user is already a RedirectResponse (from require_user)
    if isinstance(user, RedirectResponse):
        return user
    
    if not hasattr(user, "roles") or "admin" not in user.roles:
        logger.warning(f"Unauthorized admin access attempt by {user.username} to {request.url.path}")
        
        if redirect_to_login:
            return RedirectResponse(
                url=f"/login?next={request.url.path}",
                status_code=302
            )
        else:
            raise HTTPException(
                status_code=403, 
                detail="Not authorized. Admin privileges required."
            )
    
    return user
