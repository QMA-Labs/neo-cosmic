from __future__ import annotations

import os
import platform
import shutil
import sqlite3
from dataclasses import dataclass

from neo.bootstrap import Runtime
from neo.core.portable import detect_portable_layout


@dataclass(frozen=True, slots=True)
class HealthCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class ProductHealth:
    ready: bool
    checks: tuple[HealthCheck, ...]


def check_product_health(runtime: Runtime) -> ProductHealth:
    layout = detect_portable_layout()
    checks = [
        HealthCheck(
            "platform", "pass" if platform.system() == "Windows" else "warn", platform.platform()
        ),
        HealthCheck(
            "portable_mode", "pass" if layout.enabled else "warn", str(layout.root or "local mode")
        ),
        HealthCheck(
            "data_writable",
            "pass" if os.access(runtime.storage.path, os.W_OK) else "fail",
            str(runtime.storage.path),
        ),
    ]
    ollama = runtime.ollama.status()
    checks.append(
        HealthCheck("ollama", "pass" if ollama.reachable else "fail", ollama.error or "reachable")
    )
    missing = [
        model
        for model in (runtime.settings.light_model, runtime.settings.main_model)
        if model not in ollama.models
    ]
    checks.append(
        HealthCheck(
            "models",
            "pass" if not missing else "warn",
            "missing: " + ", ".join(missing) if missing else "both available",
        )
    )
    try:
        with sqlite3.connect(runtime.memory.database) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        checks.append(HealthCheck("memory", "pass" if integrity == "ok" else "fail", integrity))
    except sqlite3.Error as exc:
        checks.append(HealthCheck("memory", "fail", str(exc)))
    free = shutil.disk_usage(runtime.storage.path).free
    checks.append(
        HealthCheck(
            "free_space", "pass" if free >= 2 * 1024**3 else "warn", f"{free / 1024**3:.2f} GB"
        )
    )
    return ProductHealth(not any(check.status == "fail" for check in checks), tuple(checks))
