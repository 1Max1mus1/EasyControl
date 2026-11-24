from __future__ import annotations

import queue
import socket
import threading
import time

from .protocol import (
    ProtocolError,
    authentication,
    authentication_matches,
    receive_exact,
    receive_json,
    send_json,
)
from .server import CaptureSettings


class ControlClient:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self.frames: queue.Queue[tuple[dict, bytes]] = queue.Queue(maxsize=2)
        self.events: queue.Queue[dict] = queue.Queue()
        self.connection: socket.socket | None = None
        self.connection_lock = threading.Lock()
        self.send_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.connected = threading.Event()
        self.thread: threading.Thread | None = None
        self.settings = CaptureSettings()
        self.rtt_ms = 0.0

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="easycontrol-client", daemon=True)
        self.thread.start()
        threading.Thread(target=self._ping_loop, name="easycontrol-ping", daemon=True).start()

    def stop(self) -> None:
        self.stop_event.set()
        self.connected.clear()
        with self.connection_lock:
            connection = self.connection
        if connection:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                connection.close()
            except OSError:
                pass

    def _run(self) -> None:
        try:
            self.events.put({"type": "status", "text": f"正在连接 {self.host}:{self.port}…"})
            connection = socket.create_connection((self.host, self.port), timeout=12)
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            connection.settimeout(15)
            with self.connection_lock:
                self.connection = connection
            challenge = receive_json(connection)
            if challenge.get("type") != "challenge" or challenge.get("version") != 1:
                raise ProtocolError("被控端协议版本不兼容")
            nonce = str(challenge["nonce"])
            auth = authentication(self.password, "client", nonce, "controller")
            send_json(
                connection,
                {"type": "hello", "version": 1, "device": "controller", "auth": auth},
            )
            welcome = receive_json(connection)
            if welcome.get("type") == "error":
                raise ProtocolError(str(welcome.get("message", "被控端拒绝连接")))
            expected = authentication(self.password, "server", nonce, "host")
            if (
                welcome.get("type") != "welcome"
                or welcome.get("version") != 1
                or not authentication_matches(expected, welcome.get("auth"))
            ):
                raise ProtocolError("被控端身份认证失败")
            session = receive_json(connection)
            if session.get("type") != "session":
                raise ProtocolError("无法初始化远程画面")
            connection.settimeout(None)
            self.connected.set()
            self.events.put({"type": "connected", "host_name": session.get("host_name", "远程电脑")})
            self.update_settings(self.settings)
            self._receive_loop(connection)
        except (ConnectionError, OSError, ValueError, KeyError, ProtocolError) as exc:
            if not self.stop_event.is_set():
                self.events.put({"type": "error", "text": str(exc)})
        finally:
            self.connected.clear()
            with self.connection_lock:
                if self.connection:
                    try:
                        self.connection.close()
                    except OSError:
                        pass
                self.connection = None
            self.events.put({"type": "disconnected"})

    def _receive_loop(self, connection: socket.socket) -> None:
        count = 0
        byte_count = 0
        interval_started = time.perf_counter()
        while not self.stop_event.is_set():
            message = receive_json(connection)
            kind = message.get("type")
            if kind == "frame":
                payload = receive_exact(connection, int(message["size"]))
                count += 1
                byte_count += len(payload)
                try:
                    self.frames.put_nowait((message, payload))
                except queue.Full:
                    try:
                        self.frames.get_nowait()
                        self.frames.put_nowait((message, payload))
                    except (queue.Empty, queue.Full):
                        pass
            elif kind == "pong":
                self.rtt_ms = max(0.0, (time.time() - float(message["timestamp"])) * 1000)
            elif kind == "error":
                raise ProtocolError(str(message.get("message", "远程连接错误")))
            now = time.perf_counter()
            elapsed = now - interval_started
            if elapsed >= 1:
                self.events.put(
                    {
                        "type": "stats",
                        "fps": round(count / elapsed, 1),
                        "mbps": round(byte_count * 8 / elapsed / 1_000_000, 2),
                        "rtt": round(self.rtt_ms, 1),
                    }
                )
                count = 0
                byte_count = 0
                interval_started = now

    def _ping_loop(self) -> None:
        while not self.stop_event.is_set():
            if self.connected.wait(0.5):
                try:
                    self._send({"type": "ping", "timestamp": time.time()})
                except OSError:
                    return
                self.stop_event.wait(2)

    def _send(self, message: dict) -> None:
        if not self.connected.is_set() or not self.connection:
            return
        with self.send_lock:
            send_json(self.connection, message)

    def send_input(self, event: dict) -> None:
        try:
            self._send({"type": "input", "event": event})
        except OSError as exc:
            self.events.put({"type": "error", "text": str(exc)})

    def update_settings(self, settings: CaptureSettings) -> None:
        self.settings = settings.sanitized()
        try:
            self._send(
                {
                    "type": "settings",
                    "fps": self.settings.fps,
                    "quality": self.settings.quality,
                    "max_width": self.settings.max_width,
                }
            )
        except OSError as exc:
            self.events.put({"type": "error", "text": str(exc)})
