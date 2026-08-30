from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from neo.memory import MemoryKind, MemoryStore


class LearningEventType(StrEnum):
    CORRECTION = "correction"
    FAILURE = "failure"
    WORKFLOW = "workflow"
    TEACHING = "teaching"


@dataclass(frozen=True, slots=True)
class LearningEvent:
    id: str
    type: str
    subject: str
    before: Any
    after: Any
    context: dict[str, Any]
    confidence: float
    created_at: str


@dataclass(frozen=True, slots=True)
class SkillProposal:
    id: str
    name: str
    description: str
    steps: tuple[dict[str, Any], ...]
    evidence_events: tuple[str, ...]
    status: str
    version: int
    created_at: str


class LearningEngine:
    """Evidence-backed learning; proposals cannot execute until explicitly approved."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def record(
        self,
        event_type: LearningEventType,
        subject: str,
        *,
        before: Any = None,
        after: Any = None,
        context: dict[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> LearningEvent:
        if not subject.strip() or not 0 <= confidence <= 1:
            raise ValueError("invalid learning event")
        event = LearningEvent(
            uuid.uuid4().hex,
            event_type.value,
            subject.strip(),
            before,
            after,
            context or {},
            confidence,
            datetime.now(UTC).isoformat(),
        )
        self.memory.set(
            f"learning.event.{event.id}",
            asdict(event),
            kind=MemoryKind.LEARNED,
            confidence=confidence,
            source="learning-engine",
            evidence={"event_type": event.type},
        )
        return event

    def correct(self, subject: str, wrong: Any, correct: Any, **context: Any) -> LearningEvent:
        event = self.record(
            LearningEventType.CORRECTION,
            subject,
            before=wrong,
            after=correct,
            context=context,
        )
        self.memory.set(
            f"learned.correction.{self._slug(subject)}",
            correct,
            kind=MemoryKind.LEARNED,
            confidence=1.0,
            source="user-correction",
            evidence={"event_id": event.id, "previous": wrong},
        )
        return event

    def failure(
        self,
        subject: str,
        error: str,
        *,
        attempted_action: str,
        context: dict[str, Any] | None = None,
    ) -> LearningEvent:
        return self.record(
            LearningEventType.FAILURE,
            subject,
            before={"action": attempted_action},
            after={"error": error},
            context=context,
            confidence=1.0,
        )

    def workflow(
        self, name: str, steps: tuple[dict[str, Any], ...], *, successful: bool
    ) -> LearningEvent:
        return self.record(
            LearningEventType.WORKFLOW,
            name,
            after={"steps": steps, "successful": successful},
            confidence=0.9 if successful else 0.5,
        )

    def propose_skill(
        self,
        name: str,
        description: str,
        steps: tuple[dict[str, Any], ...],
        evidence_events: tuple[str, ...],
    ) -> SkillProposal:
        if not steps or not evidence_events:
            raise ValueError("skill proposal requires steps and evidence")
        proposal = SkillProposal(
            uuid.uuid4().hex,
            name.strip(),
            description.strip(),
            steps,
            evidence_events,
            "proposed",
            1,
            datetime.now(UTC).isoformat(),
        )
        self.memory.set(
            f"learning.skill.{proposal.id}",
            asdict(proposal),
            kind=MemoryKind.LEARNED,
            confidence=0.6,
            source="skill-evolution",
            evidence={"events": evidence_events},
        )
        return proposal

    def approve_skill(self, proposal_id: str) -> SkillProposal:
        key = f"learning.skill.{proposal_id}"
        entry = self.memory.get(key)
        if not entry:
            raise KeyError(proposal_id)
        value = {**entry.value, "status": "approved", "version": int(entry.value["version"])}
        self.memory.set(
            key,
            value,
            kind=MemoryKind.CORE,
            protected=True,
            confidence=1.0,
            source="user-approval",
            evidence=entry.evidence,
        )
        return SkillProposal(
            value["id"],
            value["name"],
            value["description"],
            tuple(value["steps"]),
            tuple(value["evidence_events"]),
            value["status"],
            value["version"],
            value["created_at"],
        )

    def consolidate(self) -> dict[str, int]:
        """Remove exact duplicate unprotected events while keeping the oldest evidence."""
        entries = [
            e
            for e in self.memory.search("learning.event.", 10_000)
            if e.key.startswith("learning.event.")
        ]
        seen: dict[str, str] = {}
        removed = 0
        for entry in sorted(entries, key=lambda item: item.created_at):
            canonical = {k: v for k, v in entry.value.items() if k not in {"id", "created_at"}}
            digest = hashlib.sha256(
                json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest()
            if digest in seen and not entry.protected:
                self.memory.forget(entry.key)
                removed += 1
            else:
                seen[digest] = entry.key
        self.memory.purge_expired()
        return {"examined": len(entries), "duplicates_removed": removed}

    @staticmethod
    def _slug(value: str) -> str:
        normalized = re.sub(r"[^\w.-]+", "-", value.casefold(), flags=re.UNICODE).strip("-")
        return normalized or hashlib.sha256(value.encode()).hexdigest()[:16]
