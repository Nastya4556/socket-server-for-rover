import inspect

from ..base_module import BaseModule

def discover_modules(package):

    classes = {}
    for name, obj in inspect.getmembers(package):
        if inspect.isclass(obj):
            if issubclass(obj, BaseModule) and obj != BaseModule:
                if getattr(obj, "ready_for_interface", False):
                    classes[name] = obj

    return classes

