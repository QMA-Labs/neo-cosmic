from __future__ import annotations

import json
import sys
import tempfile
from dataclasses import asdict, replace
from pathlib import Path

from neo.bootstrap import bootstrap
from neo.core.config import Settings
from neo.core.model_router import TaskComplexity
from neo.memory import MemoryKind


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="neo-smoke-") as temp:
        settings = replace(Settings.from_env(), data_dir=Path(temp))
        runtime = bootstrap(settings)
        written = runtime.memory.set("smoke", {"ok": True})
        read = runtime.memory.get("smoke")
        if read is None or read.value != written.value:
            raise RuntimeError("memory round-trip failed")
        ollama = runtime.ollama.status()
        core = runtime.memory.set(
            "identity.neo",
            "portable companion",
            kind=MemoryKind.CORE,
            protected=True,
            source="smoke-test",
            evidence={"verified": True},
        )
        runtime.memory.relate("identity.neo", "runs_on", "smoke", confidence=1.0)
        adaptive = runtime.router.choose(TaskComplexity.HIGH, force_refresh=True)
        result = {
            "hardware_detection": {"status": "pass", "data": runtime.hardware.to_dict()},
            "model_selection": {"status": "pass", **asdict(runtime.model)},
            "ollama_connectivity": {
                "status": "pass" if ollama.reachable else "skip",
                "models": ollama.models,
                "reason": ollama.error,
            },
            "memory_round_trip": {"status": "pass", "value": read.value},
            "adaptive_router": {"status": "pass", **asdict(adaptive)},
            "memory_brain": {
                "status": "pass",
                "protected": core.protected,
                "relations": len(runtime.memory.relations("identity.neo")),
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
