from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from neo.core.portable import configure_portable_environment, detect_portable_layout


def _load_dotenv(path: Path) -> None:
    """Load a simple .env file without overwriting exported variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    log_level: str = "INFO"
    ollama_url: str = "http://127.0.0.1:11434"
    main_model: str = "qwen3.5:9b"
    light_model: str = "qwen3.5:0.8b"
    main_min_vram_gb: float = 8.0
    main_min_ram_gb: float = 16.0
    max_load_percent: float = 85.0
    prefer_removable: bool = False

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        configure_portable_environment(detect_portable_layout())
        _load_dotenv(env_file or Path.cwd() / ".env")
        configured_data = os.getenv("NEO_DATA_DIR", "").strip()
        data_dir = (
            Path(configured_data).expanduser()
            if configured_data
            else Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share")) / "neo"
        )
        return cls(
            data_dir=data_dir,
            log_level=os.getenv("NEO_LOG_LEVEL", "INFO").upper(),
            ollama_url=os.getenv("NEO_OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
            main_model=os.getenv("NEO_MAIN_MODEL", "qwen3.5:9b"),
            light_model=os.getenv("NEO_LIGHT_MODEL", "qwen3.5:0.8b"),
            main_min_vram_gb=float(os.getenv("NEO_MAIN_MIN_VRAM_GB", "8")),
            main_min_ram_gb=float(os.getenv("NEO_MAIN_MIN_RAM_GB", "16")),
            max_load_percent=float(os.getenv("NEO_MAX_LOAD_PERCENT", "85")),
            prefer_removable=_bool_env("NEO_PREFER_REMOVABLE", False),
        )
