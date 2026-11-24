from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes

ULONG_PTR = ctypes.c_size_t


class MouseInput(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KeyboardInput(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class InputUnion(ctypes.Union):
    _fields_ = [("mouse", MouseInput), ("keyboard", KeyboardInput)]


class Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("data", InputUnion)]


KEYS = {
    "Return": 0x0D,
    "BackSpace": 0x08,
    "Tab": 0x09,
    "Escape": 0x1B,
    "space": 0x20,
    "Prior": 0x21,
    "Next": 0x22,
    "End": 0x23,
    "Home": 0x24,
    "Left": 0x25,
    "Up": 0x26,
    "Right": 0x27,
    "Down": 0x28,
    "Insert": 0x2D,
    "Delete": 0x2E,
    "Shift_L": 0xA0,
    "Shift_R": 0xA1,
    "Control_L": 0xA2,
    "Control_R": 0xA3,
    "Alt_L": 0xA4,
    "Alt_R": 0xA5,
    "Caps_Lock": 0x14,
    "Num_Lock": 0x90,
    "Scroll_Lock": 0x91,
    "Pause": 0x13,
    "Print": 0x2C,
    "Win_L": 0x5B,
    "Super_L": 0x5B,
    "Win_R": 0x5C,
    "Super_R": 0x5C,
    "Menu": 0x5D,
}
KEYS.update({f"F{number}": 0x6F + number for number in range(1, 25)})

BUTTONS = {
    "left": (0x0002, 0x0004),
    "right": (0x0008, 0x0010),
    "middle": (0x0020, 0x0040),
}


class WindowsInput:
    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(Input), ctypes.c_int)
        self.user32.SendInput.restype = wintypes.UINT
        self.user32.VkKeyScanW.argtypes = (wintypes.WCHAR,)
        self.user32.VkKeyScanW.restype = wintypes.SHORT
        self.width = self.user32.GetSystemMetrics(0)
        self.height = self.user32.GetSystemMetrics(1)
        self.pressed_keys: set[int] = set()
        self.pressed_buttons: set[str] = set()
        self.last_x = 0.5
        self.last_y = 0.5
        self.lock = threading.Lock()

    def _send(self, value: Input) -> None:
        ctypes.set_last_error(0)
        if self.user32.SendInput(1, ctypes.byref(value), ctypes.sizeof(Input)) != 1:
            raise ctypes.WinError(ctypes.get_last_error())

    def _mouse(self, x: float, y: float, flags: int, data: int = 0) -> None:
        self.last_x = max(0.0, min(1.0, x))
        self.last_y = max(0.0, min(1.0, y))
        dx = round(self.last_x * 65535)
        dy = round(self.last_y * 65535)
        value = Input(type=0)
        value.data.mouse = MouseInput(dx, dy, data, flags | 0x0001 | 0x8000, 0, 0)
        self._send(value)

    def _key(self, virtual_key: int, pressed: bool) -> None:
        value = Input(type=1)
        value.data.keyboard = KeyboardInput(virtual_key, 0, 0 if pressed else 0x0002, 0, 0)
        self._send(value)

    def virtual_key(self, keysym: str, char: str) -> int | None:
        if keysym in KEYS:
            return KEYS[keysym]
        if len(keysym) == 1 and keysym.isalnum():
            return ord(keysym.upper())
        if char and char.isprintable():
            result = self.user32.VkKeyScanW(char)
            if result != -1:
                return result & 0xFF
        return None

    def execute(self, event: dict) -> None:
        kind = event.get("type")
        with self.lock:
            if kind == "move":
                self._mouse(float(event["x"]), float(event["y"]), 0)
            elif kind in ("press", "release"):
                button = str(event["button"])
                if button not in BUTTONS:
                    return
                down, up = BUTTONS[button]
                pressed = kind == "press"
                self._mouse(float(event["x"]), float(event["y"]), down if pressed else up)
                if pressed:
                    self.pressed_buttons.add(button)
                else:
                    self.pressed_buttons.discard(button)
            elif kind == "wheel":
                self._mouse(
                    float(event["x"]),
                    float(event["y"]),
                    0x0800,
                    int(event.get("delta", 0)) * 120,
                )
            elif kind in ("key_down", "key_up"):
                virtual_key = self.virtual_key(str(event.get("key", "")), str(event.get("char", "")))
                if virtual_key is None:
                    return
                pressed = kind == "key_down"
                self._key(virtual_key, pressed)
                if pressed:
                    self.pressed_keys.add(virtual_key)
                else:
                    self.pressed_keys.discard(virtual_key)

    def release_all(self) -> None:
        with self.lock:
            for virtual_key in list(self.pressed_keys):
                try:
                    self._key(virtual_key, False)
                except OSError:
                    pass
            for button in list(self.pressed_buttons):
                try:
                    self._mouse(self.last_x, self.last_y, BUTTONS[button][1])
                except OSError:
                    pass
            self.pressed_keys.clear()
            self.pressed_buttons.clear()
