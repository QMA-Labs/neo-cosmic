from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

PORTABLE_MARKER = "NEO_PORTABLE"


@dataclass(frozen=True, slots=True)
class PortableLayout:
    enabled: bool
    root: Path | None
    data: Path | None
    models: Path | None
    backups: Path | None


def detect_portable_layout(start: Path | None = None) -> PortableLayout:
    """Detect a NEO drive without depending on its Windows drive letter."""
    if start is None:
        executable = Path(sys.executable).resolve()
        start = executable.parent if getattr(sys, "frozen", False) else Path.cwd().resolve()
    current = start.resolve()
    candidates = (current, *current.parents)
    for root in candidates:
        if (root / PORTABLE_MARKER).is_file():
            return PortableLayout(
                True,
                root,
                root / "data",
                root / "models",
                root / "backups",
            )
    return PortableLayout(False, None, None, None, None)


def configure_portable_environment(layout: PortableLayout) -> None:
    if not layout.enabled:
        return
    assert layout.data and layout.models and layout.backups
    for directory in (layout.data, layout.models, layout.backups):
        directory.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("NEO_DATA_DIR", str(layout.data))
    os.environ.setdefault("OLLAMA_MODELS", str(layout.models))
