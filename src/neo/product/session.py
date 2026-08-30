from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from neo.bootstrap import Runtime
from neo.device import DeviceProfiler, MachineProfile
from neo.memory import MemoryKind


@dataclass(frozen=True, slots=True)
class ConsentManifest:
    machine_id: str
    device_profile: bool
    screen_capture: bool
    discovery_roots: tuple[str, ...]
    agent_actions: tuple[str, ...]
    granted_at: str


class ProductSession:
    """Binds the portable brain to one host without silently expanding permissions."""

    def __init__(self, runtime: Runtime) -> None:
        self.runtime = runtime
        self.profiler = DeviceProfiler()

    def identify_host(self) -> MachineProfile:
        profile = self.profiler.capture()
        self.profiler.save(profile, self.runtime.storage.path / "profiles" / "machines")
        self.runtime.memory.set(
            "device.current_machine",
            profile.machine_id,
            kind=MemoryKind.TEMPORARY,
            source="product-session",
            ttl_seconds=86_400,
        )
        return profile

    def consent_for(self, machine_id: str) -> ConsentManifest | None:
        entry = self.runtime.memory.get(f"consent.machine.{machine_id}")
        if not entry:
            return None
        value = entry.value
        return ConsentManifest(
            value["machine_id"],
            bool(value["device_profile"]),
            bool(value["screen_capture"]),
            tuple(value["discovery_roots"]),
            tuple(value["agent_actions"]),
            value["granted_at"],
        )

    def save_consent(
        self,
        machine_id: str,
        *,
        device_profile: bool,
        screen_capture: bool = False,
        discovery_roots: tuple[Path, ...] = (),
        agent_actions: tuple[str, ...] = (),
    ) -> ConsentManifest:
        roots = tuple(str(path.expanduser().resolve()) for path in discovery_roots)
        manifest = ConsentManifest(
            machine_id,
            device_profile,
            screen_capture,
            roots,
            tuple(dict.fromkeys(agent_actions)),
            datetime.now(UTC).isoformat(),
        )
        self.runtime.memory.set(
            f"consent.machine.{machine_id}",
            asdict(manifest),
            kind=MemoryKind.CORE,
            protected=True,
            source="user-consent",
        )
        return manifest

    def revoke(self, machine_id: str) -> bool:
        return self.runtime.memory.forget(f"consent.machine.{machine_id}", force=True)
