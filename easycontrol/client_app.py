from __future__ import annotations

import io
import queue
import time
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from .client import ControlClient
from .server import CaptureSettings


class ClientApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EasyControl - 控制端")
        self.root.geometry("1100x760")
        self.root.minsize(760, 540)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.client: ControlClient | None = None
        self.remote_image: Image.Image | None = None
        self.display_image: ImageTk.PhotoImage | None = None
        self.view_rect = (0, 0, 0, 0)
        self.last_move = 0.0
        self.stats = {"fps": 0.0, "mbps": 0.0, "rtt": 0.0}

        self.host = tk.StringVar()
        self.port = tk.IntVar(value=47990)
        self.password = tk.StringVar()
        self.status = tk.StringVar(value="未连接")
        self.fps = tk.IntVar(value=15)
        self.quality = tk.IntVar(value=60)
        self.max_width = tk.IntVar(value=1280)
        self._build()
        self.root.after(15, self._poll)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill=tk.BOTH, expand=True)
        connection = ttk.LabelFrame(outer, text="连接被控电脑", padding=8)
        connection.pack(fill=tk.X)
        ttk.Label(connection, text="IP 地址").pack(side=tk.LEFT)
        ttk.Entry(connection, textvariable=self.host, width=22).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(connection, text="端口").pack(side=tk.LEFT)
        ttk.Entry(connection, textvariable=self.port, width=8).pack(side=tk.LEFT, padx=(6, 12))
        ttk.Label(connection, text="密码").pack(side=tk.LEFT)
        password_entry = ttk.Entry(connection, textvariable=self.password, show="●", width=20)
        password_entry.pack(side=tk.LEFT, padx=(6, 12))
        password_entry.bind("<Return>", lambda _: self.connect())
        self.connect_button = ttk.Button(connection, text="连接", command=self.connect)
        self.connect_button.pack(side=tk.LEFT)
        self.disconnect_button = ttk.Button(connection, text="断开", command=self.disconnect, state=tk.DISABLED)
        self.disconnect_button.pack(side=tk.LEFT, padx=8)

        settings = ttk.Frame(outer)
        settings.pack(fill=tk.X, pady=8)
        ttk.Label(settings, text="帧率").pack(side=tk.LEFT)
        ttk.Spinbox(settings, from_=2, to=30, textvariable=self.fps, width=5).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(settings, text="画质").pack(side=tk.LEFT)
        ttk.Spinbox(settings, from_=25, to=90, textvariable=self.quality, width=5).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(settings, text="最大宽度").pack(side=tk.LEFT)
        ttk.Combobox(settings, textvariable=self.max_width, values=(640, 960, 1280, 1600, 1920, 2560), width=7, state="readonly").pack(side=tk.LEFT, padx=(4, 10))
        ttk.Button(settings, text="应用", command=self.apply_settings).pack(side=tk.LEFT)
        ttk.Label(settings, textvariable=self.status, foreground="#175a9c").pack(side=tk.RIGHT)

        self.video = tk.Label(outer, background="#111", takefocus=True, highlightthickness=1, highlightbackground="#444")
        self.video.pack(fill=tk.BOTH, expand=True)
        self.video.bind("<Configure>", lambda _: self._render())
        self.video.bind("<Motion>", self._mouse_move)
        self.video.bind("<B1-Motion>", self._mouse_move)
        self.video.bind("<B2-Motion>", self._mouse_move)
        self.video.bind("<B3-Motion>", self._mouse_move)
        for number, button in ((1, "left"), (2, "middle"), (3, "right")):
            self.video.bind(f"<ButtonPress-{number}>", lambda event, b=button: self._mouse_button(event, b, True))
            self.video.bind(f"<ButtonRelease-{number}>", lambda event, b=button: self._mouse_button(event, b, False))
        self.video.bind("<MouseWheel>", self._wheel)
        self.video.bind("<KeyPress>", lambda event: self._key(event, True))
        self.video.bind("<KeyRelease>", lambda event: self._key(event, False))

    def _settings(self) -> CaptureSettings:
        return CaptureSettings(self.fps.get(), self.quality.get(), self.max_width.get()).sanitized()

    def connect(self) -> None:
        if self.client and self.client.connected.is_set():
            return
        host = self.host.get().strip()
        if not host or not self.password.get():
            messagebox.showerror("无法连接", "请填写被控端 IP 和连接密码")
            return
        try:
            port = int(self.port.get())
            self._settings()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("无法连接", str(exc))
            return
        self.client = ControlClient(host, port, self.password.get())
        self.client.settings = self._settings()
        self.client.start()
        self.connect_button.configure(state=tk.DISABLED)
        self.disconnect_button.configure(state=tk.NORMAL)

    def disconnect(self) -> None:
        if self.client:
            self.client.stop()
        self.status.set("已断开")
        self.connect_button.configure(state=tk.NORMAL)
        self.disconnect_button.configure(state=tk.DISABLED)

    def apply_settings(self) -> None:
        try:
            settings = self._settings()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("设置无效", str(exc))
            return
        self.fps.set(int(settings.fps))
        self.quality.set(settings.quality)
        self.max_width.set(settings.max_width)
        if self.client:
            self.client.update_settings(settings)

    def _poll(self) -> None:
        client = self.client
        if client:
            while True:
                try:
                    event = client.events.get_nowait()
                except queue.Empty:
                    break
                kind = event["type"]
                if kind == "connected":
                    self.status.set(f"已连接 {event['host_name']}")
                elif kind == "disconnected":
                    self.connect_button.configure(state=tk.NORMAL)
                    self.disconnect_button.configure(state=tk.DISABLED)
                    if self.status.get().startswith("已连接"):
                        self.status.set("连接已断开")
                elif kind == "stats":
                    self.stats = event
                elif kind == "error":
                    self.status.set(f"错误：{event['text']}")
                elif kind == "status":
                    self.status.set(event["text"])
            latest = None
            while True:
                try:
                    latest = client.frames.get_nowait()
                except queue.Empty:
                    break
            if latest:
                header, payload = latest
                try:
                    self.remote_image = Image.open(io.BytesIO(payload)).convert("RGB")
                    self._render()
                    self.status.set(
                        f"{header['width']}×{header['height']} · {self.stats['fps']} FPS · "
                        f"{self.stats['mbps']} Mbps · {self.stats['rtt']} ms"
                    )
                except (OSError, ValueError):
                    pass
        if self.root.winfo_exists():
            self.root.after(15, self._poll)

    def _render(self) -> None:
        if self.remote_image is None:
            return
        width = max(1, self.video.winfo_width())
        height = max(1, self.video.winfo_height())
        scale = min(width / self.remote_image.width, height / self.remote_image.height)
        display_width = max(1, round(self.remote_image.width * scale))
        display_height = max(1, round(self.remote_image.height * scale))
        resized = self.remote_image.resize((display_width, display_height), Image.Resampling.BILINEAR)
        self.display_image = ImageTk.PhotoImage(resized)
        self.video.configure(image=self.display_image)
        self.view_rect = ((width - display_width) // 2, (height - display_height) // 2, display_width, display_height)

    def _position(self, event) -> tuple[float, float] | None:
        left, top, width, height = self.view_rect
        if not width or not height:
            return None
        x = (event.x - left) / width
        y = (event.y - top) / height
        if not (0 <= x <= 1 and 0 <= y <= 1):
            return None
        return x, y

    def _mouse_move(self, event) -> None:
        now = time.monotonic()
        if now - self.last_move < 0.02:
            return
        self.last_move = now
        position = self._position(event)
        if position and self.client:
            self.client.send_input({"type": "move", "x": position[0], "y": position[1]})

    def _mouse_button(self, event, button: str, pressed: bool) -> None:
        self.video.focus_set()
        position = self._position(event)
        if position and self.client:
            self.client.send_input(
                {"type": "press" if pressed else "release", "button": button, "x": position[0], "y": position[1]}
            )

    def _wheel(self, event) -> None:
        position = self._position(event)
        if position and self.client:
            self.client.send_input(
                {"type": "wheel", "x": position[0], "y": position[1], "delta": max(-1, min(1, event.delta // 120))}
            )

    def _key(self, event, pressed: bool) -> str:
        if self.client:
            self.client.send_input(
                {"type": "key_down" if pressed else "key_up", "key": event.keysym, "char": event.char}
            )
        return "break"

    def close(self) -> None:
        if self.client:
            self.client.stop()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    ClientApp(root)
    root.mainloop()
