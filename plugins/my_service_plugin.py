from service_example import service

@service('my_service_func')
def my_service_func(param1, param2):
    return f"Service called with {param1} and {param2}"
