# -*- coding: utf-8 -*-
from __future__ import print_function
from collections import namedtuple
from functools import partial, wraps


def config(permission=-1, event=None, trigger=None, help=""):
    def wrapper(func):
        @wraps(func)
        def caller(self, *args, **kwargs):
            if "player" in kwargs and not self.__permit__(
                kwargs["player"], caller.permission
            ):
                return self.__permission_not_allowed__(
                    command=caller.triger, permission=caller.permission, *args, **kwargs
                )
            else:
                return func(self, *args, **kwargs)

        caller.event = func.__name__ if not any((event, trigger)) else event
        caller.trigger = trigger
        caller.help = help
        caller.permission = permission
        return caller

    return wrapper


class Plugin(object):
    """
    """

    MCDR_PREFIX = "!!"
    ENTRY = None

    def __init__(self):
        super(Plugin, self).__init__()
        self.server = None
        self.event_mappings = {
            event: callback for event, callback in self.generate_events()
        }
        self.trigger_mappings = {
            trigger: callback for trigger, callback in self.generate_triggers()
        }
        if self.ENTRY is None:
            raise ValueError("entry can not be None")
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, "event") and attr.event is not None:
                self.event_mappings[attr.event] = attr
            if hasattr(attr, "trigger") and attr.trigger is not None:
                self.trigger_mappings[attr.trigger] = attr
        if "on_info" not in self.event_mappings:
            self.event_mappings["on_info"] = self.__on_info__
        for event, callback in self.event_mappings.items():
            globals()[event] = partial(self.caller, event=event)

    def generate_triggers(self):
        return []

    def generate_events(self):
        return []

    def __set_server__(self, server):
        self.server = server

    def __permit__(self, player, permission):
        return True

    def __permission_not_allowed__(self, player, permission, command):
        print ("permission required")

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, "__dict__") and not hasattr(
            type(self), name
        ):
            return getattr(object.__getattribute__(self, "server"), name)
        else:
            return object.__getattribute__(self, name)

    def caller(self, server, event=None, *args, **kwargs):
        self.__set_server__(server)
        func = self.event_mappings.get(event)
        if event == "on_info":
            info = args[0]
            content = info.content[len(self.MCDR_PREFIX) :].strip()
            if not content.startswith(self.ENTRY):
                return None
            values = content[len(self.ENTRY) :].strip().split()
            return func(*values[1:], player=info.player, info=info)
        else:
            if "player" not in kwargs:
                kwargs["player"] = "@console"
            return func(*args, **kwargs)

    @config(permission=-1, envent="on_info")
    def __on_info__(self, *args, **kwargs):
        trigger = "" if not args else args[0]
        if trigger in self.trigger_mappings:
            return self.trigger_mappings[trigger](*args[1:], **kwargs)


class PluginA(Plugin):
    pass

