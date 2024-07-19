from functools import wraps

def public_route():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if request:
                request.state.public_route = True
            return await func(*args, **kwargs)
        wrapper.__public_route__ = True
        return wrapper
    return decorator