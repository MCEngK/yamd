# -*- coding: utf-8 -*-
#! /usr/bin/env python3

import importlib
import time
import json
import shutil
import re
import traceback
from enum import Enum
from subprocess import PIPE, STDOUT, Popen
import sys
from .utils import Logger, _, Rcon, curse, Priority

__CONSOLE = "@console"
RESERVED_PLAYERS = [__CONSOLE]


class Status(Enum):
    """Minecraft process status"""

    STOPPING = -1
    STOPPED = 0
    STARTING = 1
    RUNNING = 2


class Gandalf(object):
    def __init__(self, parser, server, settings, *args, **kwargs):
        self.server = server
        self.permissions = dict()
        self.settings = settings
        self.rcon = None
        self.process = None
        self.status = None
        self.logger = Logger(self)
        self.logger.set_file(settings.logging_file)
        self.parser = parser
        self.plugins = []
        self.producers = []
        self.consumers = []

    @property
    def is_running(self):
        return self.process is not None

    @property
    def is_startup(self):
        return self.status == Status.RUNNING

    def __import_file(self, filename):
        module_name = re.sub(pattern="[\\/.]", repl="_", string=filename)
        try:
            from imp import load_source

            module = load_source(module_name, filename)
        except ImportError:
            import importlib.util

            spec = importlib.util.spec_from_file_location(module_name, filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return module

    def load_plugins(self):
        plugins = self.__import_file("plugins/plugins.py")
        Plugin = getattr(plugins, "Plugin")
        self.plugins = [
            plugin
            for name in dir(plugins)
            for plugin in [getattr(plugins, name)]
            if isinstance(plugin, type)
            and issubclass(plugin, Plugin)
            and plugin is not Plugin
        ]

        # plugins =[
        #           value
        #           for value in importlib.import_module("plugins.plugins", "pluginss").__dict__.values()
        #           if isinstance(value, type) and issubclass(value, Plugin)
        #         ]

    # process management
    def startup(self):
        if self.is_running:
            self.logger.warning(_("server already started up"))
            return False

        self.logger.info(_("starting server now"))
        try:
            self.process = Popen(
                self.settings.lauch_cmd,
                cwd=self.settings.working_directory,
                stdin=PIPE,
                stdout=PIPE,
                stderr=STDOUT,
                shell=True,
            )
            self.logger.info(_("server process is starting"))
            self.status = Status.STARTING
            return True
        except:
            self.logger.error(_("lauch server failed"))
            self.logger.debug(traceback.format_exc())
        return False

    def stop(self, forced=False):
        if not self.is_running:
            self.logger.warning(_("server already stopped"))
        if not forced:
            self.execute(self.parser.STOP_COMMAND)

    @curse(priority=Priority.ADMIN)
    def wait_until(self, status, timeout=3600, tick=0.1):
        for _ in range(int(timeout / tick)):
            if self.server.status == status:
                return True
            time.sleep(tick)
        return False

    @curse(priority=Priority.ADMIN)
    def restart(self):
        self.server.stop()
        if not self.wait_until(status=Status.STOPPED):
            self.logger.error(_("restart server failed"))
        else:
            self.server.start()

    # INPUT
    def receive(self, from_stdin=False):
        source = sys.stdin if from_stdin else self.process.stdout
        while True:
            line = source.readline()
            try:
                line = line.decode(self.settings.decoding)
            except Exception as e:
                self.logger.error(
                    _("decode received text {} decoded as {} failed got {}").format(
                        line, self.settings.decoding, e
                    )
                )
            yield line.strip()

    def produce(self, from_stdin=False):
        pass

    # command executor
    @curse(priority=Priority.PLUGIN)
    def execute(self, command, ending="\n", use_rcon=False):
        if type(command) is str:
            command = (command.strip() + ending).encode(self.settings.encoding)
        self.__execute(command) if not use_rcon else self.__rcon_execute(command)

    @curse(priority=Priority.USER)
    def speak_to(self, text, player="@a", use_rcon=False):
        self.execute(
            "tellraw {} {}".format(player, json.dumps({"text": text})),
            use_rcon=use_rcon,
        )

    def __execute(self, command):
        if self.is_running:
            self.process.stdin.write(command)
            self.process.stdin.flush()
        else:
            self.logger.warning(
                _("command {} not executed while server not running").format(command)
            )

    # permissions

    @curse(priority=Priority.USER)
    def permit(
        self, player, priority=None, permission=None, permissions=(), feedback=False
    ):
        if player in RESERVED_PLAYERS:
            return True
        if player not in self.permissions:
            self.update_permissions(player=player)
        user = self.permissions[player]
        if priority is not None and priority <= user["priority"]:
            return True
        if permission is not None:
            permissions = [permission]

        for permission in permissions:
            if permission in user["permissions"]:
                return True
        if not player.startswith("@") and feedback:
            self.speak_to(
                text=_("not permitted for {} ").format(
                    " ".join(permissions) if permissions else _("lower priority")
                ),
                player=player,
            )
        return False

    @curse(priority=Priority.ADMIN)
    def load_permissions(self, filename=None):
        if filename is None:
            filename = self.settings.permissions_filename
        with open(filename, "r") as fl:
            self.permissions = json.load(fl)

    @curse(priority=Priority.ADMIN)
    def update_permissions(
        self, player, permission=None, priority=None, permissions=None
    ):
        if player not in self.permissions:
            self.permissions[player] = {"priority": 0, "permissions": []}
        if priority is not None:
            self.permissions[player]["priority"] = priority
        if permission is not None:
            permissions = [permission]
        if permissions is not None:
            self.permissions[player]["permissions"].extend(permissions)
        self.dump_permissions()

    @curse(priority=Priority.USER)
    def dump_permissions(self, filename=None):
        self.permissions = {
            username: {
                key: list(set(value)) if type(value) is list else value
                for key, value in config.items()
            }
            for username, config in self.permissions.items()
        }
        if filename is None:
            filename = self.settings.permissions_filename
        tmp_file = "{}.tmp".format(filename)
        with open(tmp_file, "w") as fl:
            json.dump(self.permissions, fl, indent=2)
        shutil.move(tmp_file, filename)

    # RCON things
    @property
    def rcon_connected(self):
        return self.rcon and self.rcon.socket

    def rcon_connect(self):
        host, port, password = (
            self.settings.rcon_host,
            self.settings.rcon_port,
            self.settings.rcon_password,
        )
        if (
            not all((host, port, password))
            or self.rcon_connected
            or not self.is_startup
        ):
            return

        try:
            rcon = Rcon(host, port, password, self.logger)
            success = self.rcon.connect()
            msg = _("rcon failed: wrong password")
            if success:
                self.rcon = rcon
                msg = _("rcon connected")
            self.logger.info(msg)
        except Exception as e:
            self.logger.warning(_("rcon connection failed %s"), e)

    def rcon_disconnect(self):
        if self.rcon_connected:
            self.rcon.disconnect()
        self.rcon = None

    def __rcon_execute(self, command):
        if self.rcon_connected:
            return self.rcon.execute(command)
        return None
