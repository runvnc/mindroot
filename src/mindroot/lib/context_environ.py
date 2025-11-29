"""
context_environ.py

Patches os.environ and os.getenv to automatically check for a 'context' variable 
in the call stack. If context exists and has the requested key (either as 
context[key] or context.env[key]), that value is returned instead of the actual 
environment variable.

Usage:
    import mindroot.lib.context_environ  # Just importing patches os.environ and os.getenv
    
    # Or explicitly:
    from mindroot.lib.context_environ import patch_environ, unpatch_environ
    patch_environ()
    
    # Now any function with a 'context' parameter will have env lookups check context first:
    def my_function(data, context=None):
        api_key = os.environ.get('API_KEY')  # Checks context first!
        api_key2 = os.getenv('API_KEY')       # Also checks context first!
        return api_key
    
    ctx = {'API_KEY': 'secret-per-session-key'}
    my_function(data, context=ctx)  # Returns 'secret-per-session-key'
    my_function(data)                # Returns actual os.environ['API_KEY']

Performance:
    ~1.1-1.3x overhead when context is found in nearby frames
    ~2x overhead worst case (no context, searches max_depth frames)
"""

import sys
import os
from typing import Any, Optional

__all__ = ['patch_environ', 'unpatch_environ', 'is_patched']

_original_environ = None
_original_getenv = None
_is_patched = False
_max_depth = 10


def _find_in_context(key: str, skip_frames: int = 2) -> tuple[bool, Any]:
    """
    Search call stack for 'context' variable and look up key.
    Returns (found: bool, value: Any)
    
    Args:
        key: The environment variable name to look up
        skip_frames: Number of frames to skip (caller's caller by default)
    """
    try:
        frame = sys._getframe(skip_frames)
        depth = 0
        
        while frame is not None and depth < _max_depth:
            ctx = frame.f_locals.get('context')
            
            if ctx is not None:
                # Try context as dict
                if isinstance(ctx, dict):
                    if key in ctx:
                        return True, ctx[key]
                # Try context.env as dict
                elif hasattr(ctx, 'env'):
                    env = ctx.env
                    if isinstance(env, dict) and key in env:
                        return True, env[key]
            
            frame = frame.f_back
            depth += 1
            
    except (ValueError, AttributeError):
        pass
    
    return False, None


def _context_aware_getenv(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Context-aware replacement for os.getenv.
    Checks the call stack for a 'context' variable first.
    """
    found, value = _find_in_context(key, skip_frames=2)
    if found:
        return value
    return _original_getenv(key, default)


class ContextAwareEnviron:
    """
    A wrapper around os.environ that checks the call stack for a 'context' 
    variable and uses its values as overrides.
    
    Supports context as:
    - A dict: context['KEY']
    - An object with .env dict: context.env['KEY']
    """
    
    def __init__(self, original_environ):
        self._original = original_environ
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable, checking context first."""
        found, value = _find_in_context(key, skip_frames=2)
        if found:
            return value
        return self._original.get(key, default)
    
    def __getitem__(self, key: str) -> str:
        """Get an environment variable, checking context first. Raises KeyError if not found."""
        found, value = _find_in_context(key, skip_frames=2)
        if found:
            return value
        return self._original[key]
    
    def __setitem__(self, key: str, value: str) -> None:
        """Set an environment variable (always sets on real environ)."""
        self._original[key] = value
    
    def __delitem__(self, key: str) -> None:
        """Delete an environment variable."""
        del self._original[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists (checks context first, then real environ)."""
        found, _ = _find_in_context(key, skip_frames=2)
        if found:
            return True
        return key in self._original
    
    def __iter__(self):
        """Iterate over environment variable names."""
        return iter(self._original)
    
    def __len__(self) -> int:
        """Return number of environment variables."""
        return len(self._original)
    
    def __repr__(self) -> str:
        return f"ContextAwareEnviron({self._original!r})"
    
    def keys(self):
        return self._original.keys()
    
    def values(self):
        return self._original.values()
    
    def items(self):
        return self._original.items()
    
    def setdefault(self, key: str, default: str = None) -> str:
        return self._original.setdefault(key, default)
    
    def pop(self, key: str, *args) -> str:
        return self._original.pop(key, *args)
    
    def update(self, *args, **kwargs):
        return self._original.update(*args, **kwargs)
    
    def copy(self) -> dict:
        return self._original.copy()
    
    # Pass through any other attributes to the original
    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)


def patch_environ(max_depth: int = 10) -> None:
    """
    Patch os.environ and os.getenv to be context-aware.
    
    Args:
        max_depth: Maximum number of stack frames to search for 'context'.
                   Lower values are faster but may miss context in deeply nested calls.
    """
    global _original_environ, _original_getenv, _is_patched, _max_depth
    
    if _is_patched:
        return
    
    _max_depth = max_depth
    _original_environ = os.environ
    _original_getenv = os.getenv
    
    os.environ = ContextAwareEnviron(_original_environ)
    os.getenv = _context_aware_getenv
    
    _is_patched = True


def unpatch_environ() -> None:
    """Restore os.environ and os.getenv to their original state."""
    global _original_environ, _original_getenv, _is_patched
    
    if not _is_patched:
        return
    
    os.environ = _original_environ
    os.getenv = _original_getenv
    
    _original_environ = None
    _original_getenv = None
    _is_patched = False


def is_patched() -> bool:
    """Check if os.environ and os.getenv are currently patched."""
    return _is_patched


# Auto-patch on import
patch_environ()
