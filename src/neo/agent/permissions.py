from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from neo.memory import MemoryKind, MemoryStore


class PermissionScope(StrEnum):
    ONCE = "once"
    ALWAYS = "always"
    PROJECT = "project"
    FOLDER = "folder"


@dataclass(frozen=True, slots=True)
class PermissionGrant:
    action: str
    scope: str
    target: str | None
    granted_at: str
    consumed: bool = False


class PermissionStore:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def grant(
        self, action: str, scope: PermissionScope, target: str | None = None
    ) -> PermissionGrant:
        if scope in {PermissionScope.PROJECT, PermissionScope.FOLDER} and not target:
            raise ValueError("scoped permission requires a target")
        normalized = str(Path(target).expanduser().resolve()) if target else None
        grant = PermissionGrant(action, scope.value, normalized, datetime.now(UTC).isoformat())
        self.memory.set(
            self._key(action, scope, normalized),
            asdict(grant),
            kind=MemoryKind.CORE,
            protected=True,
            source="user-consent",
        )
        return grant

    def authorize(self, action: str, target: Path | None = None) -> bool:
        candidates = [
            (PermissionScope.ONCE, None),
            (PermissionScope.ALWAYS, None),
        ]
        resolved = target.expanduser().resolve() if target else None
        if resolved:
            candidates.extend(
                (scope, str(parent))
                for parent in (resolved, *resolved.parents)
                for scope in (PermissionScope.PROJECT, PermissionScope.FOLDER)
            )
        for scope, candidate_target in candidates:
            entry = self.memory.get(self._key(action, scope, candidate_target))
            if not entry or entry.value.get("consumed"):
                continue
            if scope == PermissionScope.ONCE:
                consumed = {**entry.value, "consumed": True}
                self.memory.set(entry.key, consumed, kind=MemoryKind.CORE, source="permission-use")
            return True
        return False

    @staticmethod
    def _key(action: str, scope: PermissionScope, target: str | None) -> str:
        safe_target = (target or "global").replace("\\", "/")
        return f"permissions.agent.{action}.{scope.value}.{safe_target}"
