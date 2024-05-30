from json import *  # noqa: F403, CIR107


# Default to compact serialization.

def __wrap(func):
    def wrapper(*args, **kwargs):
        new_kwargs = {"separators": (",", ":")}
        new_kwargs.update(kwargs)
        return func(*args, **new_kwargs)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


dump = __wrap(dump)  # noqa: F405
dumps = __wrap(dumps)  # noqa: F405
del __wrap
