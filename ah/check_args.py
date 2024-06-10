def check_empty_args(args, kwargs):
    if len(args) > 0:
        if all([arg is None or arg == '' for arg in args]):
            return True
    if len(kwargs) > 0:
        if all([kwargs[key] is None or kwargs[key] == '' for key in kwargs]):
            return True
    return False


