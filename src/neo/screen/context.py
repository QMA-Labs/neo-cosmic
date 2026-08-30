from __future__ import annotations

import base64
import ctypes
import os
import platform
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Event

import mss
import mss.tools

from neo.core.ollama_client import OllamaClient
from neo.memory import MemoryKind, MemoryStore


@dataclass(frozen=True, slots=True)
class ActiveApp:
    process: str | None
    title: str | None
    category: str


@dataclass(frozen=True, slots=True)
class ScreenContext:
    app: ActiveApp
    captured_at: float
    monitor: int
    width: int
    height: int
    image_base64: str


class ScreenIntelligence:
    """Consent-gated, on-demand screen context with no persistent screenshot by default."""

    MIN_CAPTURE_INTERVAL = 2.0

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory
        self._last_capture = 0.0

    def grant(self) -> None:
        self.memory.set(
            "permissions.screen_capture",
            True,
            kind=MemoryKind.CORE,
            protected=True,
            source="user-consent",
        )

    def revoke(self) -> None:
        self.memory.set(
            "permissions.screen_capture",
            False,
            kind=MemoryKind.CORE,
            source="user-consent",
        )

    def capture(self, monitor: int = 1) -> ScreenContext:
        permission = self.memory.get("permissions.screen_capture")
        if not permission or permission.value is not True:
            raise PermissionError("screen capture permission has not been granted")
        now = time.monotonic()
        if now - self._last_capture < self.MIN_CAPTURE_INTERVAL:
            raise RuntimeError("screen capture rate limit exceeded")
        with mss.mss() as session:
            if monitor < 0 or monitor >= len(session.monitors):
                raise ValueError("invalid monitor index")
            target = session.monitors[monitor]
            shot = session.grab(target)
            encoded = base64.b64encode(mss.tools.to_png(shot.rgb, shot.size)).decode("ascii")
        self._last_capture = now
        return ScreenContext(
            self.active_app(), time.time(), monitor, shot.width, shot.height, encoded
        )

    def analyze(
        self,
        client: OllamaClient,
        model: str,
        question: str,
        *,
        monitor: int = 1,
        context_size: int = 8192,
        cancel_event: Event | None = None,
    ) -> str:
        context = self.capture(monitor)
        prompt = (
            "You are NEO Screen Intelligence. Analyze only visible information. "
            "Never infer passwords, hidden data, identity, or facts not shown. "
            f"Active app category: {context.app.category}. User question: {question}"
        )
        return client.chat_with_image(
            model,
            prompt,
            context.image_base64,
            context_size=context_size,
            cancel_event=cancel_event,
        )

    @staticmethod
    def active_app() -> ActiveApp:
        if platform.system() == "Windows":
            return ScreenIntelligence._windows_active_app()
        title = ScreenIntelligence._linux_window_title()
        return ActiveApp(None, title, ScreenIntelligence._categorize(title or ""))

    @staticmethod
    def _windows_active_app() -> ActiveApp:
        try:
            user32 = ctypes.windll.user32
            handle = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(handle)
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(handle, buffer, length + 1)
            process_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(handle, ctypes.byref(process_id))
            process = ScreenIntelligence._process_name(process_id.value)
            return ActiveApp(
                process,
                buffer.value or None,
                ScreenIntelligence._categorize(f"{process} {buffer.value}"),
            )
        except (AttributeError, OSError):
            return ActiveApp(None, None, "unknown")

    @staticmethod
    def _process_name(process_id: int) -> str | None:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"(Get-Process -Id {int(process_id)} -ErrorAction Stop).ProcessName",
        ]
        try:
            return (
                subprocess.run(
                    command, check=True, capture_output=True, text=True, timeout=2
                ).stdout.strip()
                or None
            )
        except (OSError, subprocess.SubprocessError):
            return None

    @staticmethod
    def _linux_window_title() -> str | None:
        try:
            return (
                subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=2,
                ).stdout.strip()
                or None
            )
        except (OSError, subprocess.SubprocessError):
            return None

    @staticmethod
    def _categorize(value: str) -> str:
        value = value.casefold()
        categories = {
            "code": ("code", "visual studio", "pycharm", "jetbrains"),
            "browser": ("chrome", "firefox", "edge", "brave"),
            "creative": ("premiere", "photoshop", "after effects", "davinci"),
            "office": ("excel", "word", "powerpoint", "libreoffice"),
            "terminal": ("terminal", "powershell", "cmd.exe", "windows terminal"),
        }
        for category, markers in categories.items():
            if any(
                re.search(rf"(?<![a-z0-9]){re.escape(marker)}(?![a-z0-9])", value)
                for marker in markers
            ):
                return category
        return "unknown"


def secure_temporary_png(image_base64: str) -> Path:
    """Compatibility helper for tools requiring a file; caller must unlink it."""
    descriptor, name = tempfile.mkstemp(prefix="neo-screen-", suffix=".png")
    os.close(descriptor)
    path = Path(name)
    path.write_bytes(base64.b64decode(image_base64))
    return path
