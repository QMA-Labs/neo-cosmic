from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(level: str, data_dir: Path) -> logging.Logger:
    log_dir = data_dir / "logs"
    root = logging.getLogger()
    root.setLevel(level)
    if not any(getattr(handler, "_neo_handler", False) for handler in root.handlers):
        formatter = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s", "%Y-%m-%dT%H:%M:%S"
        )
        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        stream._neo_handler = True  # type: ignore[attr-defined]
        root.addHandler(stream)
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_dir / "neo.log", encoding="utf-8")
            file_handler.setFormatter(formatter)
            file_handler._neo_handler = True  # type: ignore[attr-defined]
            root.addHandler(file_handler)
        except OSError:
            logging.getLogger("neo").warning("Log directory is read-only: %s", log_dir)
    return logging.getLogger("neo")
