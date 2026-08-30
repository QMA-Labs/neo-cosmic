from __future__ import annotations

import getpass
import re
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from neo.memory import MemoryKind, MemoryStore


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold().strip()
    return re.sub(r"\s+", " ", value)


@dataclass(frozen=True, slots=True)
class PersonProfile:
    id: str
    display_name: str
    aliases: tuple[str, ...]
    attributes: dict[str, Any]
    confidence: float
    source: str
    updated_at: str


class PeopleEngine:
    """Explicit, evidence-backed people profiles; never guesses identity from filenames."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def create(
        self,
        display_name: str,
        *,
        aliases: tuple[str, ...] = (),
        attributes: dict[str, Any] | None = None,
        confidence: float = 1.0,
        source: str = "user",
    ) -> PersonProfile:
        if not display_name.strip():
            raise ValueError("display name must not be empty")
        existing = self.find(display_name)
        if existing:
            return self.update(existing.id, aliases=aliases, attributes=attributes or {})
        person_id = uuid.uuid4().hex
        profile = PersonProfile(
            person_id,
            display_name.strip(),
            tuple(dict.fromkeys(alias.strip() for alias in aliases if alias.strip())),
            attributes or {},
            confidence,
            source,
            datetime.now(UTC).isoformat(),
        )
        self._save(profile)
        return profile

    def update(
        self,
        person_id: str,
        *,
        display_name: str | None = None,
        aliases: tuple[str, ...] = (),
        attributes: dict[str, Any] | None = None,
    ) -> PersonProfile:
        current = self.get(person_id)
        if current is None:
            raise KeyError(person_id)
        merged_aliases = tuple(
            dict.fromkeys((*current.aliases, *(a.strip() for a in aliases if a.strip())))
        )
        merged_attributes = {**current.attributes, **(attributes or {})}
        updated = PersonProfile(
            current.id,
            (display_name or current.display_name).strip(),
            merged_aliases,
            merged_attributes,
            current.confidence,
            current.source,
            datetime.now(UTC).isoformat(),
        )
        self._save(updated)
        return updated

    def get(self, person_id: str) -> PersonProfile | None:
        entry = self.memory.get(f"people.profile.{person_id}")
        return self._from_dict(entry.value) if entry else None

    def find(self, name_or_alias: str) -> PersonProfile | None:
        wanted = _normalize(name_or_alias)
        for entry in self.memory.search("people.profile.", limit=1000):
            if not entry.key.startswith("people.profile."):
                continue
            profile = self._from_dict(entry.value)
            names = {
                _normalize(profile.display_name),
                *(_normalize(alias) for alias in profile.aliases),
            }
            if wanted in names:
                return profile
        return None

    def list(self) -> list[PersonProfile]:
        return [
            self._from_dict(entry.value)
            for entry in self.memory.search("people.profile.", limit=1000)
            if entry.key.startswith("people.profile.")
        ]

    def propose_owner(self) -> PersonProfile:
        """Create a low-confidence candidate; caller/UI must ask the user to confirm it."""
        username = getpass.getuser().strip() or "Unknown"
        existing = self.find(username)
        if existing:
            return existing
        return self.create(
            username,
            aliases=("device owner candidate",),
            confidence=0.35,
            source="system-proposal",
        )

    def import_vcard(self, content: str) -> list[PersonProfile]:
        profiles = []
        for block in re.findall(r"BEGIN:VCARD(.*?)END:VCARD", content, re.DOTALL | re.IGNORECASE):
            name_match = re.search(r"^FN(?:;[^:]*)?:(.+)$", block, re.MULTILINE | re.IGNORECASE)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            attributes: dict[str, Any] = {}
            emails = re.findall(r"^EMAIL(?:;[^:]*)?:(.+)$", block, re.MULTILINE | re.IGNORECASE)
            phones = re.findall(r"^TEL(?:;[^:]*)?:(.+)$", block, re.MULTILINE | re.IGNORECASE)
            if emails:
                attributes["emails"] = tuple(value.strip() for value in emails)
            if phones:
                attributes["phones"] = tuple(value.strip() for value in phones)
            profiles.append(
                self.create(
                    name,
                    attributes=attributes,
                    confidence=0.8,
                    source="vcard-import",
                )
            )
        return profiles

    def _save(self, profile: PersonProfile) -> None:
        self.memory.set(
            f"people.profile.{profile.id}",
            asdict(profile),
            kind=MemoryKind.CORE if profile.source == "user" else MemoryKind.LEARNED,
            confidence=profile.confidence,
            protected=profile.source == "user",
            source=profile.source,
            evidence={"identity_confirmed": profile.source == "user"},
        )

    @staticmethod
    def _from_dict(value: dict[str, Any]) -> PersonProfile:
        return PersonProfile(
            value["id"],
            value["display_name"],
            tuple(value.get("aliases", ())),
            value.get("attributes", {}),
            float(value.get("confidence", 1)),
            value.get("source", "unknown"),
            value["updated_at"],
        )
