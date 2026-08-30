from pathlib import Path

from neo.core.config import Settings
from neo.core.hardware import HardwareInfo
from neo.core.model_router import AdaptiveModelRouter, TaskComplexity


def test_high_complexity_can_promote_cpu_model() -> None:
    hardware = HardwareInfo(8, 5, 32, 20, 20, None, None, None)
    router = AdaptiveModelRouter(Settings(data_dir=Path("data")), refresh_seconds=999)
    assert router.choose(hardware=hardware).model == "qwen3.5:0.8b"
    promoted = router.choose(TaskComplexity.HIGH, hardware=hardware)
    assert promoted.model == "qwen3.5:9b"
    assert promoted.tier == "compatibility"


def test_safe_fallback_is_light() -> None:
    router = AdaptiveModelRouter(Settings(data_dir=Path("data")))
    decision = router.safe_fallback("missing model")
    assert decision.tier == "fallback"
    assert decision.context_size == 4096
