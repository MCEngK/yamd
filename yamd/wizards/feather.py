from ..utils import Plugin, plugin, Priority, _
import json
from functools import partial


class Feather(Plugin):
    """a plugin to do whitelist things"""

    NAME = "whitelist"
    AUTHOR = "MCEngK"
    CONTACT = "<None>"
    VERSION = "0.0.1"
    WHITELIST_FILE = "whitelist.json"
    PROGRAM = "whitelist"

    def get_whiltelist(self):
        with open(self.WHITELIST_FILE) as wl:
            return [item["name"] for item in json.load(wl)]

    @plugin(
        priority=Priority.USER,
        trigger="list",
        usage=_("\t:list all players in whitelist"),
    )
    def list_all(self, player, *args, **kwargs):
        names = self.get_whiltelist()
        self.speak_to(
            player=player,
            text=_("whitelisted {} players: {}").format(len(names), ", ".join(names)),
        )

    @plugin(priority=Priority.USER, trigger="check", usage=_("<player>\t: check if <player> was whitelisted"))
    def check(self, player, target, *args, **kwargs):
        self.speak_to(
            player=player,
            text=_("{} {}in whitelist").format(
                target, "" if target in self.get_whiltelist() else _("not ")
            ),
        )
    
    def generate_triggers(self):
        def execute(cmd, msg, player, *args, **kwargs):
            self.execute("{} {}".format(self.PROGRAM, cmd))
            self.speak_to(player=player, text=msg)

        def multi_execute(cmd, msg, player, *args, **kwargs):
            for user in args:
                execute(cmd, msg.format(user), player)

        for trigger, msg, priority, usage in [
            ("reload", _("whitelist was reloaded"), Priority.HELPER, _("\t:reaload whiltelist")),
            ("on", _("whitelist was enabled"), Priority.ADMIN, _("\t:enable whitelist")),
            ("off", _("whitelist was disabled"), Priority.ADMIN, _("\t: disable whitelist")),
            ("add", _("{} was whitelisted"), Priority.ADMIN, _("<player>\t:whitelist <player>")),
            ("drop", _("{} was unwhitelisted"), Priority.ADMIN, _("<player>\t:unwhitelist <player>")),
        ]:
            executor = execute if "{}" not in msg else multi_execute
            yield trigger, plugin(priority=priority, trigger=trigger, usage=usage)(
                partial(executor, cmd=trigger, msg=msg)
            )


