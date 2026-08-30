from __future__ import annotations

from dataclasses import dataclass

from neo.core.config import Settings
from neo.core.hardware import HardwareInfo, detect_hardware
from neo.core.logging import configure_logging
from neo.core.model_router import AdaptiveModelRouter, ModelDecision
from neo.core.ollama_client import OllamaClient
from neo.core.storage import StorageLocation, resolve_data_location
from neo.memory import MemoryStore


@dataclass(slots=True)
class Runtime:
    settings: Settings
    storage: StorageLocation
    hardware: HardwareInfo
    model: ModelDecision
    ollama: OllamaClient
    memory: MemoryStore
    router: AdaptiveModelRouter


def bootstrap(settings: Settings | None = None) -> Runtime:
    settings = settings or Settings.from_env()
    storage = resolve_data_location(settings.data_dir, settings.prefer_removable)
    logger = configure_logging(settings.log_level, storage.path)
    hardware = detect_hardware()
    router = AdaptiveModelRouter(settings)
    model = router.choose(hardware=hardware)
    memory = MemoryStore(storage.path / "memory" / "neo.sqlite3")
    logger.info("NEO initialized: model=%s reason=%s", model.model, model.reason)
    return Runtime(
        settings=settings,
        storage=storage,
        hardware=hardware,
        model=model,
        ollama=OllamaClient(settings.ollama_url),
        memory=memory,
        router=router,
    )
