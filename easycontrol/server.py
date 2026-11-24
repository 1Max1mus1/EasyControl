from __future__ import annotations

import io
import platform
import queue
import socket
import threading
import time
import uuid
from dataclasses import dataclass

from PIL import Image, ImageGrab

from .protocol import (
    ProtocolError,
    authentication,
    authentication_matches,
    receive_json,
    send_json,
)
from .windows_input import WindowsInput


@dataclass
class CaptureSettings:
    fps: float = 15.0
    quality: int = 60
    max_width: int = 1280

    def sanitized(self) -> CaptureSettings:
        return CaptureSettings(
            fps=max(2.0, min(30.0, float(self.fps))),
            quality=max(25, min(90, int(self.quality))),
            max_width=max(640, min(3840, int(self.max_width))),
        )


class HostServer:
    def __init__(self, password: str, port: int = 47990, settings: CaptureSettings | None = None):
        if not password:
            raise ValueError("必须设置连接密码")
        self.password = password
        self.port = port
        self.settings = (settings or CaptureSettings()).sanitized()
        self.settings_lock = threading.Lock()
        self.events: queue.Queue[dict] = queue.Queue()
        self.stop_event = threading.Event()
        self.listener: socket.socket | None = None
        self.active_connection: socket.socket | None = None
        self.active_lock = threading.Lock()
        self.send_lock = threading.Lock()
        self.accept_thread: threading.Thread | None = None
        self.running = False

    def emit(self, kind: str, **values) -> None:
        self.events.put({"type": kind, **values})

    def start(self) -> None:
        if self.running:
            return
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("0.0.0.0", self.port))
        listener.listen(2)
        listener.settimeout(1)
        self.listener = listener
        self.port = int(listener.getsockname()[1])
        self.stop_event.clear()
        self.running = True
        self.accept_thread = threading.Thread(target=self._accept_loop, name="easycontrol-host", daemon=True)
        self.accept_thread.start()
        self.emit("status", text=f"等待控制端连接，端口 {self.port}")

    def stop(self) -> None:
        self.running = False
        self.stop_event.set()
        for sock in (self.listener, self.active_connection):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
        self.emit("status", text="已停止")

    def update_settings(self, settings: CaptureSettings) -> None:
        with self.settings_lock:
            self.settings = settings.sanitized()

    def current_settings(self) -> CaptureSettings:
        with self.settings_lock:
            return CaptureSettings(self.settings.fps, self.settings.quality, self.settings.max_width)

    def _accept_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                connection, address = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.emit("status", text=f"正在验证 {address[0]}…")
            self._handle_client(connection, address)

    def _handle_client(self, connection: socket.socket, address: tuple) -> None:
        session_stop = threading.Event()
        injector = WindowsInput()
        with connection:
            try:
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                connection.settimeout(45)
                nonce = uuid.uuid4().hex + uuid.uuid4().hex
                send_json(connection, {"type": "challenge", "version": 1, "nonce": nonce})
                hello = receive_json(connection)
                expected = authentication(self.password, "client", nonce, "controller")
                if (
                    hello.get("type") != "hello"
                    or hello.get("version") != 1
                    or not authentication_matches(expected, hello.get("auth"))
                ):
                    send_json(connection, {"type": "error", "message": "连接密码错误"})
                    self.emit("status", text=f"已拒绝 {address[0]}：密码错误")
                    return
                auth = authentication(self.password, "server", nonce, "host")
                send_json(connection, {"type": "welcome", "version": 1, "auth": auth})
                send_json(connection, {"type": "session", "host_name": platform.node()})
                connection.settimeout(None)
                with self.active_lock:
                    self.active_connection = connection
                self.emit("connected", address=address[0])
                receiver = threading.Thread(
                    target=self._receive_inputs,
                    args=(connection, injector, session_stop),
                    name="easycontrol-input",
                    daemon=True,
                )
                receiver.start()
                self._capture_loop(connection, session_stop)
            except (ConnectionError, OSError, ValueError, KeyError, ProtocolError) as exc:
                if not self.stop_event.is_set():
                    self.emit("error", text=str(exc))
            finally:
                session_stop.set()
                injector.release_all()
                with self.active_lock:
                    if self.active_connection is connection:
                        self.active_connection = None
                self.emit("disconnected")

    def _capture_loop(self, connection: socket.socket, session_stop: threading.Event) -> None:
        sequence = 0
        while not self.stop_event.is_set() and not session_stop.is_set():
            started = time.perf_counter()
            settings = self.current_settings()
            image = ImageGrab.grab(all_screens=False)
            if settings.max_width and image.width > settings.max_width:
                height = round(image.height * settings.max_width / image.width)
                image = image.resize((settings.max_width, height), Image.Resampling.BILINEAR)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=settings.quality, optimize=False)
            payload = buffer.getvalue()
            captured_at = time.time()
            with self.send_lock:
                send_json(
                    connection,
                    {
                        "type": "frame",
                        "sequence": sequence,
                        "timestamp": captured_at,
                        "width": image.width,
                        "height": image.height,
                        "size": len(payload),
                    },
                )
                connection.sendall(payload)
            sequence += 1
            elapsed = time.perf_counter() - started
            session_stop.wait(max(0.0, 1.0 / settings.fps - elapsed))

    def _receive_inputs(
        self, connection: socket.socket, injector: WindowsInput, session_stop: threading.Event
    ) -> None:
        try:
            while not self.stop_event.is_set() and not session_stop.is_set():
                event = receive_json(connection)
                kind = event.get("type")
                if kind == "input":
                    injector.execute(event["event"])
                elif kind == "ping":
                    with self.send_lock:
                        send_json(connection, {"type": "pong", "timestamp": event.get("timestamp")})
                elif kind == "settings":
                    current = self.current_settings()
                    self.update_settings(
                        CaptureSettings(
                            event.get("fps", current.fps),
                            event.get("quality", current.quality),
                            event.get("max_width", current.max_width),
                        )
                    )
                    self.emit("settings", settings=self.current_settings())
                elif kind == "disconnect":
                    return
        except (ConnectionError, OSError, ValueError, KeyError, ProtocolError):
            return
        finally:
            session_stop.set()
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    @staticmethod
    def local_addresses() -> list[str]:
        addresses = set()
        try:
            for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                address = item[4][0]
                if not address.startswith("127."):
                    addresses.add(address)
        except socket.gaierror:
            pass
        return sorted(addresses)
