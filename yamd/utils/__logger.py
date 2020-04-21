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
