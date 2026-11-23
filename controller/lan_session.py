"""Exchange board actions over a single TCP connection on the local network."""

import json
import queue
import socket
import threading
import time


LAN_PORT = 47650
PROTOCOL = ["police-voleur", 1]
MAX_LINE = 256


class LanSession:
    def __init__(self, address=None, port=LAN_PORT, role=None):
        self.events = queue.Queue()
        self.outgoing = queue.Queue()
        self.stopped = threading.Event()
        self.listener = None
        self.role = role if address is None else None
        if address is None and self.role is None:
            self.role = "police"
        if address is None:
            listener = socket.socket()
            try:
                listener.bind(("", port))
                listener.listen(1)
                listener.settimeout(0.2)
            except OSError:
                listener.close()
                raise
            self.listener = listener
        threading.Thread(target=self.run, args=(address, port), daemon=True).start()

    def close(self):
        self.stopped.set()

    def send(self, action):
        self.outgoing.put(action)

    def accept(self):
        with self.listener as listener:
            while not self.stopped.is_set():
                try:
                    connection, _ = listener.accept()
                    return connection
                except socket.timeout:
                    continue
        return None

    @staticmethod
    def write(connection, message):
        connection.sendall(json.dumps(message).encode("ascii") + b"\n")

    def run(self, address, port):
        try:
            connection = (
                self.accept() if address is None
                else socket.create_connection((address, port), timeout=5)
            )
            if connection is not None:
                with connection:
                    self.exchange(connection)
        except (OSError, ValueError) as error:
            if not self.stopped.is_set():
                self.events.put(("error", str(error)))

    def exchange(self, connection):
        connection.settimeout(0.1)
        self.write(connection, PROTOCOL + [self.role or "choose"])
        ready = False
        handshake_deadline = time.monotonic() + 5
        buffer = b""
        while not self.stopped.is_set():
            if not ready and time.monotonic() >= handshake_deadline:
                raise ValueError("L’autre joueur ne répond pas.")
            while not self.outgoing.empty():
                self.write(connection, self.outgoing.get_nowait())
            try:
                chunk = connection.recv(1024)
            except socket.timeout:
                continue
            if not chunk:
                raise ValueError("L’autre joueur a quitté la partie.")
            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                if len(line) > MAX_LINE:
                    raise ValueError("Message LAN trop long.")
                message = json.loads(line)
                if not ready:
                    if (
                        not isinstance(message, list)
                        or len(message) != 3
                        or message[:2] != PROTOCOL
                        or message[2] not in ("police", "thief", "choose")
                        or (
                            self.role is not None
                            and message[2] != "choose"
                            and message[2] == self.role
                        )
                    ):
                        raise ValueError("Version du jeu incompatible.")
                    if self.role is None:
                        if message[2] not in ("police", "thief"):
                            raise ValueError("L’hébergeur n’a pas choisi de rôle.")
                        self.role = "thief" if message[2] == "police" else "police"
                    peer_role = (
                        ("thief" if self.role == "police" else "police")
                        if message[2] == "choose" else message[2]
                    )
                    ready = True
                    self.events.put(("ready", peer_role))
                else:
                    self.events.put(("action", message))
            if len(buffer) > MAX_LINE:
                raise ValueError("Message LAN trop long.")
