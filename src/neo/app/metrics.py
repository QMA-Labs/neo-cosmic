from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import psutil


@dataclass(frozen=True, slots=True)
class LiveMetrics:
    cpu_percent: float
    ram_percent: float
    ram_used_gb: float
    storage_percent: float
    storage_free_gb: float
    network_down_mbps: float
    network_up_mbps: float
    battery_percent: float | None
    power_plugged: bool | None
    gpu_percent: float | None
    vram_used_gb: float | None
    vram_total_gb: float | None
    gpu_temperature_c: float | None
    gpu_power_w: float | None


class MetricsSampler:
    def __init__(self, storage_path: Path) -> None:
        self.storage_path = storage_path
        self._last_net = psutil.net_io_counters()
        self._last_time = time.monotonic()

    def sample(self) -> LiveMetrics:
        now = time.monotonic()
        elapsed = max(0.1, now - self._last_time)
        network = psutil.net_io_counters()
        down = (network.bytes_recv - self._last_net.bytes_recv) * 8 / elapsed / 1_000_000
        up = (network.bytes_sent - self._last_net.bytes_sent) * 8 / elapsed / 1_000_000
        self._last_net, self._last_time = network, now
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.storage_path))
        battery = psutil.sensors_battery()
        gpu = self._gpu_metrics()
        return LiveMetrics(
            psutil.cpu_percent(),
            memory.percent,
            round(memory.used / 1024**3, 1),
            disk.percent,
            round(disk.free / 1024**3, 1),
            round(max(0.0, down), 2),
            round(max(0.0, up), 2),
            round(battery.percent, 0) if battery else None,
            battery.power_plugged if battery else None,
            *gpu,
        )

    @staticmethod
    def _gpu_metrics() -> tuple[float | None, ...]:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=1.5,
                check=True,
            )
            values = [float(value.strip()) for value in result.stdout.splitlines()[0].split(",")]
            utilization, used_mb, total_mb, temperature, power = values
            return utilization, used_mb / 1024, total_mb / 1024, temperature, power
        except (FileNotFoundError, subprocess.SubprocessError, ValueError, IndexError):
            return None, None, None, None, None
