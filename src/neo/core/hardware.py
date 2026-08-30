from __future__ import annotations

import shutil
import subprocess
from dataclasses import asdict, dataclass

import psutil


@dataclass(frozen=True, slots=True)
class HardwareInfo:
    cpu_count: int
    cpu_load_percent: float
    ram_total_gb: float
    ram_available_gb: float
    ram_load_percent: float
    gpu_name: str | None = None
    vram_total_gb: float | None = None
    gpu_load_percent: float | None = None
    vram_available_gb: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _nvidia_info() -> tuple[str | None, float | None, float | None, float | None]:
    if not shutil.which("nvidia-smi"):
        return None, None, None, None
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        first = result.stdout.splitlines()[0]
        name, memory_mb, free_mb, load = (part.strip() for part in first.split(",", 3))
        return (
            name,
            round(float(memory_mb) / 1024, 2),
            round(float(free_mb) / 1024, 2),
            float(load),
        )
    except (OSError, subprocess.SubprocessError, ValueError, IndexError):
        return None, None, None, None


def detect_hardware() -> HardwareInfo:
    memory = psutil.virtual_memory()
    gpu_name, vram_gb, vram_available_gb, gpu_load = _nvidia_info()
    return HardwareInfo(
        cpu_count=psutil.cpu_count(logical=True) or 1,
        cpu_load_percent=psutil.cpu_percent(interval=0.1),
        ram_total_gb=round(memory.total / 1024**3, 2),
        ram_available_gb=round(memory.available / 1024**3, 2),
        ram_load_percent=float(memory.percent),
        gpu_name=gpu_name,
        vram_total_gb=vram_gb,
        gpu_load_percent=gpu_load,
        vram_available_gb=vram_available_gb,
    )
