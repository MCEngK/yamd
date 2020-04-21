import logging
from .__utils import _


def curse(priority, **kwargs):
    def wrapper(obj):
        kwargs["priority"] = priority
        kwargs["cursed"] = True
        obj.__dict__.update(kwargs)
        return obj

    return wrapper


class Curse(object):
    def __init__(self, target, priority, **kwargs):
        curse(**kwargs)(self)
        self.__target = target
        self.__priority = priority

    def __getattribute__(self, name):
        target = object.__getattribute__(self, "__target")
        if not hasattr(target, name):
            raise RuntimeError(_("{} not found from {}".format(name, target)))
        attr = getattr(target, name)
        if not hasattr(attr, "cursed"):
            raise RuntimeError(
                _("attribute {} from {} was not cursed").format(name, target)
            )

        if object.__getattribute__(self, "__priority") >= attr.priority:
            return attr
        else:
            logging.debug(_("lower priority while get attribute {}").format(name))
            return lambda *args, **kwargs: None if callable(attr) else None
