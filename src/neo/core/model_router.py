from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum

from neo.core.config import Settings
from neo.core.hardware import HardwareInfo, detect_hardware


class TaskComplexity(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class ModelDecision:
    model: str
    tier: str
    reason: str
    context_size: int = 8192
    gpu_layers: int = 0
    keep_alive: str = "5m"


def select_model(
    hardware: HardwareInfo,
    settings: Settings,
    complexity: TaskComplexity = TaskComplexity.NORMAL,
) -> ModelDecision:
    overloaded = (
        max(hardware.cpu_load_percent, hardware.ram_load_percent) >= settings.max_load_percent
    )
    enough_host_ram = hardware.ram_total_gb >= 12 and hardware.ram_available_gb >= 4
    required_total_vram = max(7.5, settings.main_min_vram_gb - 0.5)
    available_vram = hardware.vram_available_gb or hardware.vram_total_gb or 0
    enough_vram = (
        hardware.vram_total_gb is not None
        and hardware.vram_total_gb >= required_total_vram
        and available_vram >= 6.5
        and (hardware.gpu_load_percent or 0) < settings.max_load_percent
    )
    if overloaded:
        return ModelDecision(
            settings.light_model, "eco", "system load is above safe threshold", 4096, 0, "2m"
        )
    if enough_host_ram and enough_vram:
        context = 16384 if hardware.ram_available_gb >= 12 and available_vram >= 7.5 else 8192
        return ModelDecision(
            settings.main_model,
            "pro",
            "sufficient free RAM and GPU VRAM",
            min(context, 8192) if complexity == TaskComplexity.LOW else context,
            -1,
            "10m",
        )
    if (
        hardware.ram_available_gb >= settings.main_min_ram_gb
        and hardware.gpu_name is None
        and complexity == TaskComplexity.HIGH
    ):
        return ModelDecision(
            settings.main_model,
            "compatibility",
            "high-complexity task using slower CPU inference",
            8192,
            0,
            "2m",
        )
    reasons = []
    if not enough_host_ram:
        reasons.append("host RAM is below the safe 9B threshold")
    if hardware.gpu_name is not None and not enough_vram:
        reasons.append("GPU VRAM/load is unsuitable")
    if hardware.gpu_name is None:
        reasons.append("no dedicated GPU available")
    return ModelDecision(
        settings.light_model,
        "light",
        "; ".join(reasons) or "safe fallback",
        8192 if hardware.ram_available_gb >= 8 else 4096,
    )


class AdaptiveModelRouter:
    """Re-evaluates compute safely without oscillating between loaded models."""

    def __init__(self, settings: Settings, refresh_seconds: float = 30.0) -> None:
        self.settings = settings
        self.refresh_seconds = refresh_seconds
        self._decision: ModelDecision | None = None
        self._checked_at = 0.0

    @property
    def decision(self) -> ModelDecision:
        return self.choose()

    def choose(
        self,
        complexity: TaskComplexity = TaskComplexity.NORMAL,
        *,
        force_refresh: bool = False,
        hardware: HardwareInfo | None = None,
    ) -> ModelDecision:
        now = time.monotonic()
        stale = now - self._checked_at >= self.refresh_seconds
        if self._decision is None or force_refresh or stale or complexity == TaskComplexity.HIGH:
            self._decision = select_model(hardware or detect_hardware(), self.settings, complexity)
            self._checked_at = now
        return self._decision

    def safe_fallback(self, reason: str) -> ModelDecision:
        self._decision = ModelDecision(self.settings.light_model, "fallback", reason, 4096, 0, "1m")
        self._checked_at = time.monotonic()
        return self._decision
