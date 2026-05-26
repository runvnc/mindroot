from .api_key_manager import api_key_manager

__all__ = ['router', 'mod', 'api_key_manager']


def __getattr__(name):
    """Lazy-load router/mod so CLI imports don't pull FastAPI route deps.

    The MindRoot CLI imports ``mindroot.coreplugins.api_keys.api_key_manager``
    to create keys. Python executes this package __init__ first, so eager
    router imports can break CLI-only operations if server route dependencies
    are not importable in that context.
    """
    if name == 'router':
        from .router import router
        return router
    if name == 'mod':
        from . import mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
