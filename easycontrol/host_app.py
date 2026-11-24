from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox, ttk

from .server import CaptureSettings, HostServer


class HostApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EasyControl - 被控端")
        self.root.geometry("570x480")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.server: HostServer | None = None
        self.port = tk.IntVar(value=47990)
        self.password = tk.StringVar()
        self.fps = tk.IntVar(value=15)
        self.quality = tk.IntVar(value=60)
        self.max_width = tk.IntVar(value=1280)
        self.status = tk.StringVar(value="尚未启动")
        self.addresses = tk.StringVar(value="本机 IP：" + "、".join(HostServer.local_addresses()))
        self._build()
        self.root.after(100, self._poll)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill=tk.BOTH, expand=True)
        ttk.Label(outer, text="让这台电脑接受远程控制", font=("Segoe UI", 15, "bold")).pack(anchor=tk.W, pady=(0, 14))
        connection = ttk.LabelFrame(outer, text="连接设置", padding=12)
        connection.pack(fill=tk.X)
        ttk.Label(connection, text="监听端口").grid(row=0, column=0, sticky=tk.W, pady=6)
        ttk.Entry(connection, textvariable=self.port, width=12).grid(row=0, column=1, sticky=tk.W, padx=12)
        ttk.Label(connection, text="连接密码").grid(row=1, column=0, sticky=tk.W, pady=6)
        ttk.Entry(connection, textvariable=self.password, show="●", width=28).grid(row=1, column=1, sticky=tk.W, padx=12)
        ttk.Label(connection, text="控制端需要填写相同密码；不要把端口直接暴露到公网", foreground="#666").grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        capture = ttk.LabelFrame(outer, text="画面设置", padding=12)
        capture.pack(fill=tk.X, pady=14)
        ttk.Label(capture, text="帧率（2–30）").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(capture, from_=2, to=30, textvariable=self.fps, width=8).grid(row=0, column=1, sticky=tk.W, padx=12)
        ttk.Label(capture, text="JPEG 画质（25–90）").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(capture, from_=25, to=90, textvariable=self.quality, width=8).grid(row=1, column=1, sticky=tk.W, padx=12)
        ttk.Label(capture, text="最大画面宽度").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(capture, textvariable=self.max_width, values=(640, 960, 1280, 1600, 1920, 2560), width=8, state="readonly").grid(row=2, column=1, sticky=tk.W, padx=12)

        actions = ttk.Frame(outer)
        actions.pack(fill=tk.X)
        self.start_button = ttk.Button(actions, text="启动被控服务", command=self.start)
        self.start_button.pack(side=tk.LEFT)
        self.stop_button = ttk.Button(actions, text="停止", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=8)
        ttk.Button(actions, text="应用画面设置", command=self.apply_settings).pack(side=tk.RIGHT)
        ttk.Label(outer, textvariable=self.addresses, wraplength=520).pack(anchor=tk.W, pady=(16, 5))
        ttk.Label(outer, textvariable=self.status, foreground="#175a9c", wraplength=520).pack(anchor=tk.W, pady=5)
        ttk.Label(outer, text="跨城市使用时，请填写 Tailscale 分配给这台电脑的 IP。", foreground="#666").pack(anchor=tk.W, pady=(12, 0))

    def _settings(self) -> CaptureSettings:
        return CaptureSettings(self.fps.get(), self.quality.get(), self.max_width.get()).sanitized()

    def start(self) -> None:
        try:
            if not self.password.get():
                raise ValueError("请设置连接密码")
            self.server = HostServer(self.password.get(), int(self.port.get()), self._settings())
            self.server.start()
        except (OSError, ValueError, tk.TclError) as exc:
            self.server = None
            messagebox.showerror("无法启动", str(exc))
            return
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)

    def stop(self) -> None:
        if self.server:
            self.server.stop()
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)

    def apply_settings(self) -> None:
        try:
            settings = self._settings()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("设置无效", str(exc))
            return
        self.fps.set(int(settings.fps))
        self.quality.set(settings.quality)
        self.max_width.set(settings.max_width)
        if self.server:
            self.server.update_settings(settings)
            self.status.set("画面设置已应用")

    def _poll(self) -> None:
        if self.server:
            while True:
                try:
                    event = self.server.events.get_nowait()
                except queue.Empty:
                    break
                kind = event["type"]
                if kind == "status":
                    self.status.set(event["text"])
                elif kind == "connected":
                    self.status.set(f"控制端已连接：{event['address']}")
                    self.stop_button.configure(state=tk.NORMAL)
                elif kind == "disconnected":
                    if self.server and self.server.running:
                        self.status.set("控制端已断开，等待新连接…")
                elif kind == "error":
                    self.status.set(f"连接错误：{event['text']}")
                elif kind == "settings":
                    settings = event["settings"]
                    self.fps.set(int(settings.fps))
                    self.quality.set(settings.quality)
                    self.max_width.set(settings.max_width)
        if self.root.winfo_exists():
            self.root.after(100, self._poll)

    def close(self) -> None:
        if self.server:
            self.server.stop()
        self.root.destroy()


def run() -> None:
    root = tk.Tk()
    HostApp(root)
    root.mainloop()
