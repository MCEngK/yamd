# -*- coding: utf-8 -*-

from functools import partial, wraps
from .__utils import format_permission, GANDALF, _
from .__curse import curse


def plugin(priority=-1, event=None, trigger=None, usage=""):
    def wrapper(func):
        @wraps(func)
        def doer(self, *args, **kwargs):
            player = kwargs.get("player", None)
            permissions = self.get_permissions()
            if self.permit(
                player=player, priority=priority, permissions=permissions, feedbak=True
            ):
                return func(self, *args, **kwargs)

        evt = func.__name__ if not any((event, trigger)) else event
        return curse(priority=priority, event=evt, trigger=trigger, usage=usage)(doer)

    return wrapper


class Plugin(object):
    NAME = None
    AUTHOR = None
    CONTACT = None
    VERSION = "0.0.0"

    def __init__(self, gandalf, *args, **kwargs):
        self.gandalf = gandalf
        self.event_mappings = {
            event: callback for event, callback in self.generate_events()
        }
        self.trigger_mappings = {
            trigger: callback for trigger, callback in self.generate_triggers()
        }
        if self.NAME is None:
            raise ValueError(_("NAME cannot be None"))
        for name in dir(self):
            attr = getattr(self, name)
            if hasattr(attr, "event") and attr.event is not None:
                self.event_mappings[attr.event] = attr
            if hasattr(attr, "trigger") and attr.trigger is not None:
                self.trigger_mappings[attr.trigger] = attr

        self.__usage__ = self.__build_usage()

    def generate_triggers(self):
        return []

    def generate_events(self):
        return []

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, "__dict__") and not hasattr(
            type(self), name
        ):
            return getattr(object.__getattribute__(self, "gandalf"), name)
        else:
            return object.__getattribute__(self, name)

    def get_permissions(self, event=None, trigger=None):
        permissions = [self.NAME]
        if event is not None:
            permissions.append(format_permission(self.NAME, event))
        if trigger is not None:
            permissions.append(format(self.NAME, trigger))

    def usage(self):
        return self.__usage__

    def __build_usage(self):
        usage = _(
            "-----<< {name} v{version} >>----\n"
            "    created by {author}\n"
            "    contact to {contact}\n\n"
            "usage:\n\n"
        ).format(
            name=self.NAME,
            version=self.VERSION,
            author=self.AUTHOR,
            contact=self.CONTACT,
        )

        template = "    {}{} {}".format(GANDALF, self.NAME, "{trigger} {usage}")

        return usage + "\n".join(
            template.format(trigger=trigger, usage=callback.usage)
            for trigger, callback in self.trigger_mappings.items()
        )
