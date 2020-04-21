from ..utils import Plugin, plugin, Priority


class Feather(Plugin):
    NAME = "whitelist"
    AUTHOR = "MCEngK"
    CONTACT = "<None>"
    VERSION = "0.0.1"

    @plugin(
        priority=Priority.USER,
        trigger="list",
        usage="\t:show all player in the whitelist",
    )
    def list_all(self, *args, **kwargs):
        pass
