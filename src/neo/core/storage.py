from __future__ import annotations

import os
import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True, slots=True)
class StorageLocation:
    path: Path
    removable: bool
    reason: str


def _is_writable(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.W_OK)


def removable_candidates() -> list[Path]:
    candidates: list[Path] = []
    for partition in psutil.disk_partitions(all=False):
        mount = Path(partition.mountpoint)
        opts = set(partition.opts.split(","))
        likely_removable = "removable" in opts or str(mount).startswith(("/media/", "/run/media/"))
        if platform.system() == "Windows":
            try:
                import ctypes

                likely_removable = ctypes.windll.kernel32.GetDriveTypeW(str(mount)) == 2
            except (AttributeError, OSError):
                likely_removable = False
        if likely_removable and _is_writable(mount):
            candidates.append(mount)
    return sorted(set(candidates))


def resolve_data_location(configured: Path, prefer_removable: bool = False) -> StorageLocation:
    if prefer_removable:
        candidates = removable_candidates()
        if candidates:
            location = candidates[0] / "NEO"
            location.mkdir(parents=True, exist_ok=True)
            return StorageLocation(location, True, "writable removable storage detected")
    try:
        configured.mkdir(parents=True, exist_ok=True)
        probe = configured / ".neo-write-probe"
        probe.touch(exist_ok=True)
        probe.unlink(missing_ok=True)
        return StorageLocation(configured, False, "configured local data directory")
    except OSError:
        identity = os.getenv("USERNAME") or os.getenv("USER") or "user"
        fallback = Path(tempfile.gettempdir()) / f"neo-{identity}"
        fallback.mkdir(parents=True, exist_ok=True)
        return StorageLocation(fallback, False, "temporary fallback: configured path is read-only")
