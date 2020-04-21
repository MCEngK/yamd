_ = lambda s: s

from functools import wraps
from enum import IntEnum
import logging

GANDALF = "#!"


def format_permission(name, value):
    return "{}@{}".format(name, value)


def retry(times=3, logger=None):
    def wrapper(func):
        @wraps
        def doer(*args, **kwargs):
            for _ in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if logger is not None:
                        logger.exception(e)

        return doer

    return wrapper


class Priority(IntEnum):
    NONE = -1
    VISITOR = 0
    USER = 1
    HELPER = 2
    PLUGIN = 2
    ADMIN = 3
    CONSOLE = 4
