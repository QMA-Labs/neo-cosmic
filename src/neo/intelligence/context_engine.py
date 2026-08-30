from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from neo.memory import MemoryKind, MemoryStore


class ContextEngine:
    """Retrieval and explicit learning over the user's permission-gated local memory."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def remember_turn(self, role: str, text: str) -> None:
        self.memory.set(
            f"conversation.{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.{uuid.uuid4().hex[:8]}",
            {"role": role, "text": text[:12_000]},
            kind=MemoryKind.LEARNED,
            confidence=1.0,
            source="conversation",
        )

    def learn_from_history(self, limit: int = 500) -> int:
        learned_before = len(self.memory.search("user.fact.", 10_000))
        entries = [
            entry
            for entry in self.memory.search("conversation.", limit)
            if entry.key.startswith("conversation.") and isinstance(entry.value, dict)
        ]
        for entry in entries:
            if entry.value.get("role") == "user":
                self.learn_explicit(str(entry.value.get("text", "")))
        learned_after = len(self.memory.search("user.fact.", 10_000))
        return max(0, learned_after - learned_before)

    def cached_answer(self, query: str) -> str | None:
        entry = self.memory.get(self._cache_key(query))
        return str(entry.value) if entry else None

    def cache_answer(self, query: str, answer: str) -> None:
        self.memory.set(
            self._cache_key(query),
            answer[:20_000],
            kind=MemoryKind.LEARNED,
            confidence=0.9,
            source="local-answer-cache",
        )

    @staticmethod
    def _cache_key(query: str) -> str:
        normalized = " ".join(query.casefold().split())
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        return f"answer.cache.v2.{digest}"

    def learn_explicit(self, text: str) -> bool:
        learned = False
        age = re.search(r"(?:من\s*)?(\d{1,3})\s*سالمه", text)
        if age:
            self._store_user_fact(f"سن: {age.group(1)}")
            learned = True
        interest = re.search(r"من(?: از)?\s+(.+?)\s+(?:رو |را )?(?:دوست دارم|خیلی دوست دارم)", text)
        if interest:
            self._store_user_fact(f"علاقه: {interest.group(1).strip()}")
            learned = True
        goal = re.search(r"(?:میخوام|می‌خوام|هدفم اینه که)\s+(.+)", text)
        if goal:
            self._store_user_fact(f"هدف: {goal.group(1).strip()}")
            learned = True
        patterns = (
            r"^(?:یادت باشه|به خاطر بسپار|remember that)\s+(.+)$",
            r"^(?:اسم من|من هستم|my name is)\s*[:،]?\s*(.+)$",
        )
        for pattern in patterns:
            match = re.match(pattern, text.strip(), re.IGNORECASE)
            if not match:
                continue
            fact = match.group(1).strip()
            self._store_user_fact(fact)
            learned = True
        return learned

    def _store_user_fact(self, fact: str) -> None:
        existing = {str(entry.value) for entry in self.memory.search("user.fact.", 1000)}
        if fact in existing:
            return
        self.memory.set(
            f"user.fact.{uuid.uuid4().hex}",
            fact,
            kind=MemoryKind.CORE,
            protected=True,
            confidence=1.0,
            source="user-explicit",
        )

    def answer_personal(self, query: str) -> str | None:
        normalized = query.casefold()
        facts = self.known_about_user(100)
        if "چند سالم" in normalized or "سن من" in normalized:
            for fact in facts:
                match = re.search(r"\b(\d{1,3})\b", fact)
                if match:
                    return f"طبق چیزی که خودت گفتی، {match.group(1)} سالته."
        if "چی دوست دارم" in normalized or "علاقه" in normalized:
            related = [fact.removeprefix("علاقه: ") for fact in facts if fact.startswith("علاقه:")]
            if related:
                return "طبق حافظه‌ام: " + "، ".join(related[:8])
        return None

    def build(self, query: str, *, limit: int = 12, max_chars: int = 10_000) -> str:
        words = [word for word in re.findall(r"[\w.-]{3,}", query.casefold()) if len(word) > 2]
        candidates = []
        candidates.extend(self.memory.search("user.fact.", 30))
        candidates.extend(self.memory.search("identity.", 10))
        local_file_intent = any(
            marker in query.casefold()
            for marker in (
                "فایل",
                "پوشه",
                "پروژه",
                "کد",
                "file",
                "folder",
                "project",
                "code",
            )
        )
        if local_file_intent:
            for word in words[:6]:
                candidates.extend(self.memory.search(word, limit))
        unique = {}
        for entry in candidates:
            if entry.key.startswith(("permissions.", "learning.event.")):
                continue
            if entry.key.startswith("discovery.file.") and not local_file_intent:
                continue
            unique.setdefault(entry.key, entry)
        lines = []
        for entry in list(unique.values())[:limit]:
            value = str(entry.value)
            lines.append(f"- {entry.key}: {value[:1200]}")
        return "\n".join(lines)[:max_chars]

    def known_about_user(self, limit: int = 20) -> list[str]:
        facts = []
        for entry in self.memory.list(1000):
            if entry.key == "identity.owner" or entry.key.startswith("user.fact."):
                facts.append(str(entry.value))
            if len(facts) >= limit:
                break
        return facts

    def find_files(self, query: str, limit: int = 12) -> list[str]:
        words = [word for word in re.findall(r"[\w.-]{2,}", query.casefold())]
        found: list[str] = []
        for word in words:
            for entry in self.memory.search(word, limit=limit * 2):
                if not entry.key.startswith("discovery.file.") or not isinstance(entry.value, dict):
                    continue
                path = entry.value.get("path")
                if path and path not in found:
                    found.append(path)
                if len(found) >= limit:
                    return found
        return found

    def discovery_summary(self) -> str:
        report = self.memory.get("discovery.last_report")
        entries = [
            entry
            for entry in self.memory.list(20_000)
            if entry.key.startswith("discovery.file.") and isinstance(entry.value, dict)
        ]
        categories: dict[str, int] = {}
        for entry in entries:
            category = str(entry.value.get("category", "unknown"))
            categories[category] = categories.get(category, 0) + 1
        category_text = "، ".join(f"{key}: {value}" for key, value in sorted(categories.items()))
        scanned = report.value.get("scanned", 0) if report and isinstance(report.value, dict) else 0
        return (
            f"آخرین بررسی تمام شده: {scanned} مسیر بررسی و {len(entries)} فایل مفید "
            f"در حافظه ثبت شده است. دسته‌ها: {category_text or 'هنوز موردی ثبت نشده'}"
        )
