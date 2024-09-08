import json

def check_empty_args(args, kwargs=None):
    if not isinstance(args, list):
        args = [args]
    empty_args = False
    empty_kwargs = False
    has_kwargs = (kwargs is not None)

    if len(args) > 0:
        if all([arg is None or arg == '' for arg in args]):
            empty_args = True
    if has_kwargs:
        if len(kwargs) > 0:
            if all([kwargs[key] is None or kwargs[key] == '' for key in kwargs]):
                empty_kwargs = True
    if not has_kwargs:
        return empty_args
    else:
        return empty_args and empty_kwargs


