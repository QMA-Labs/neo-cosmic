from pathlib import Path

from neo.core.config import Settings
from neo.core.hardware import HardwareInfo
from neo.core.model_router import select_model


def hardware(**overrides: object) -> HardwareInfo:
    values = {
        "cpu_count": 8,
        "cpu_load_percent": 20.0,
        "ram_total_gb": 32.0,
        "ram_available_gb": 20.0,
        "ram_load_percent": 35.0,
        "gpu_name": "GPU",
        "vram_total_gb": 12.0,
        "gpu_load_percent": 10.0,
    }
    values.update(overrides)
    return HardwareInfo(**values)  # type: ignore[arg-type]


def test_selects_main_with_resources() -> None:
    decision = select_model(hardware(), Settings(data_dir=Path("data")))
    assert decision.model == "qwen3.5:9b"


def test_selects_light_on_low_memory() -> None:
    decision = select_model(
        hardware(ram_available_gb=4.0, vram_total_gb=4.0), Settings(data_dir=Path("data"))
    )
    assert decision.model == "qwen3.5:0.8b"


def test_selects_light_under_load() -> None:
    decision = select_model(hardware(cpu_load_percent=99.0), Settings(data_dir=Path("data")))
    assert decision.tier == "eco"


def test_cpu_default_uses_light_model() -> None:
    decision = select_model(
        hardware(gpu_name=None, vram_total_gb=None, gpu_load_percent=None),
        Settings(data_dir=Path("data")),
    )
    assert decision.tier == "light"


def test_rtx_4060_laptop_with_16gb_ram_selects_pro() -> None:
    decision = select_model(
        hardware(
            ram_total_gb=15.5,
            ram_available_gb=7.0,
            gpu_name="NVIDIA GeForce RTX 4060 Laptop GPU",
            vram_total_gb=8.0,
            vram_available_gb=7.1,
            gpu_load_percent=8.0,
        ),
        Settings(data_dir=Path("data")),
    )
    assert decision.model == "qwen3.5:9b"
    assert decision.tier == "pro"


def test_busy_rtx_4060_safely_uses_light_model() -> None:
    decision = select_model(
        hardware(
            ram_total_gb=15.5,
            ram_available_gb=7.0,
            gpu_name="NVIDIA GeForce RTX 4060 Laptop GPU",
            vram_total_gb=8.0,
            vram_available_gb=2.0,
            gpu_load_percent=95.0,
        ),
        Settings(data_dir=Path("data")),
    )
    assert decision.model == "qwen3.5:0.8b"
