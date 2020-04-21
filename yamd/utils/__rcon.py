# -*- coding: utf-8 -*-
import socket
import struct
import time
from threading import RLock
import struct
from enum import Enum

from .__utils import _, retry


class PacketType(Enum):
    COMMAND_RESPONSE = 0
    COMMAND_REQUEST = 2
    LOGIN_REQUEST = 3
    LOGIN_FAIL = -1
    ENDING_PACKET = 100


class Packet(object):
    def __init__(self, packet_type=None, payload=None):
        self.packet_id = 0
        self.packet_type = packet_type
        self.payload = payload

    def flush(self):
        data = struct.pack("<ii", self.packet_id, self.packet_type) + bytes(
            self.payload + "\x00\x00", encoding="utf8"
        )
        return struct.pack("<i", len(data)) + data


class Rcon(object):
    BUFFER_SIZE = 2 ** 10

    def __init__(self, address, port, password, logger=None):
        self.logger = logger
        self.address = address
        self.port = port
        self.password = password
        self.socket = None
        self.lock = RLock()

    def __del__(self):
        self.disconnect()

    def send(self, data):
        if type(data) is Packet:
            data = data.flush()
        self.socket.send(data)
        time.sleep(0.03)  # MC-72390

    def __receive(self, length):
        data = bytes()
        while len(data) < length:
            data += self.socket.recv(min(self.BUFFER_SIZE, length - len(data)))
        return data

    def receive(self):
        length = struct.unpack("<i", self.__receive(4))[0]
        data = self.__receive(length)
        packet = Packet()
        packet.packet_id = struct.unpack("<i", data[0:4])[0]
        packet.packet_type = struct.unpack("<i", data[4:8])[0]
        packet.payload = data[8:-2].decode("utf8")
        return packet

    def connect(self):
        if self.socket is not None:
            return False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.address, self.port))
        self.send(Packet(PacketType.LOGIN_REQUEST, self.password))
        success = self.receive().packet_id != PacketType.LOGIN_FAIL
        if not success:
            self.disconnect()
        return success

    def disconnect(self):
        if self.socket is not None:
            self.socket.close()
        self.socket = None

    @retry(times=3)
    def execute(self, command):
        self.lock.acquire()
        try:
            self.send(Packet(PacketType.COMMAND_REQUEST, command))
            self.send(Packet(PacketType.ENDING_PACKET, "lol"))
            result = ""
            while True:
                packet = self.receive()
                if packet.payload == "Unknown request {}".format(
                    hex(PacketType.ENDING_PACKET)[2:]
                ):
                    break
                result += packet.payload
            return result
        except:
            self.disconnect()
            self.connect()
            raise
        finally:
            self.lock.release()
        return None


if __name__ == "__main__":
    rcon = Rcon("localhost", 25575, "password")
    print("Login success? ", rcon.connect())
    while True:
        print("->", rcon.execute(input("<- ")))
