import logging
import sys
import time
import os
import zipfile
import itertools
from logging.handlers import TimedRotatingFileHandler
from functools import wraps

file_logger_formatter = logging.Formatter(
    "[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console_logger_formatter = logging.Formatter(
    "[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
)
def encode_text(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

_ = lambda s: s


class Logger(object):
    def __getattribute__(self, name):
        if name in ("log", "debug", "info", "warning", "critical", "error", "setLevel"):
            return object.__getattribute__(
                object.__getattribute__(self, "logger"), name
            )
        return object.__getattribute__(self, name)

    def __init__(self, owner, level=logging.INFO):
        self.file_handler = None
        self.logger = logging.getLogger(type(owner).__name__)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_logger_formatter)

        self.logger.addHandler(console_handler)
        self.logger.setLevel(level)

    def set_file(self, filename):
        if self.file_handler is not None:
            self.logger.removeHandler(self.file_handler)
        directory = os.path.dirname(filename)
        if not os.path.isdir(directory):
            os.makedirs(directory)
        if os.path.isfile(filename):
            update_time = time.strftime(
                "%Y-%m-%d", time.localtime(os.stat(filename).st_mtime)
            )
            for counter in itertools.count():
                zip_file_name = "{}/{}-{}.zip".format(
                    os.path.dirname(filename), update_time, counter
                )
                if os.path.exists(zip_file_name):
                    break
            zip_file = zipfile.ZipFile(zip_file_name, "w")
            zip_file.write(
                filename,
                arcname=os.path.basename(filename),
                compress_type=zipfile.ZIP_DEFLATED,
            )
            zip_file.close()
            os.remove(filename)
        self.file_handler = TimedRotatingFileHandler(filename)
        self.file_handler.setFormatter(file_logger_formatter)
        self.logger.addHandler(self.file_handler)


def retry(times=3, logger=None):
    def wrapper(func):
        @wraps
        def doer(*args, **kwargs):
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if logger is not None:
                        logger.exception(e)

        return doer

    return wrapper


# class Wizard(object):
    
#     def __init__(self, source, owner, logger=None):
#         self.source = source
#         self.owner = owner
#         self.logger = logger
        
#     def __getattribute__(self, name):
#         logger = object.__getattribute__(self, "logger")
#         owner = object.__getattribute__(self, "owner")
#         source = object.__getattribute__(self, "source")
#         logger = logger if logger is not None else logging
#         if not hasattr(source, name):
#             logger.debug(_("{} not found from {}").format(name, source))
#         else:
#             target =  getattr(source, name)
            
#         logger.debug(_("{} accessing attribute of {}").format(owner, target))
#         return getattr(target, name)
    
from enum import IntEnum

class Priority(IntEnum):
    NONE = -1
    VISITOR = 0
    USER = 1
    HELPER = 2
    PLUGIN = 2
    ADMIN = 3
    CONSOLE = 4
    
    
    
def curse(priority, **kwargs):
    def wrapper(obj):
        kwargs["priority"] = priority
        obj.__dict__.update(kwargs)
        return obj
    return wrapper


class Curser(object):

    def __init__(self, target, priority, **kwargs):
        curse(**kwargs)(self)
        self.__target = target
        self.__priority = priority
        
    def __getattribute__(self, name):
        target = object.__getattribute__(self, "__target")
        if not hasattr(target, name):
            raise RuntimeError(_("{} not found from {}".format(name, target)))
        attr = getattr(target, name)
        if not hasattr(attr, "priority"):
            raise RuntimeError(_("attribute {} from {} was not cursed").format(name, target))
        
        if object.__getattribute__(self, "__priority") >= attr.priority:
            return attr
        else:
            logging.debug(_("lower priority while get attribute {}").format(name))
            return lambda *args, **kwargs: None if hasattr(attr, "func_name") else None