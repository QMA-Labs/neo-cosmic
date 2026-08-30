from __future__ import annotations

import hashlib
import os
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from neo.memory import MemoryKind, MemoryStore

DEFAULT_EXCLUDES = frozenset(
    {
        ".git",
        ".svn",
        ".hg",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".cache",
        "AppData",
        "$Recycle.Bin",
        "System Volume Information",
        "Windows",
        "proc",
        "sys",
        "dev",
        "run",
        "snap",
        "lost+found",
    }
)
TEXT_EXTENSIONS = frozenset(
    {
        ".txt",
        ".md",
        ".rst",
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".ini",
        ".csv",
    }
)
PROJECT_MARKERS = frozenset(
    {
        "pyproject.toml",
        "package.json",
        "Cargo.toml",
        "go.mod",
        "pom.xml",
        "build.gradle",
        "*.sln",
        "*.csproj",
    }
)


@dataclass(frozen=True, slots=True)
class DiscoveryPolicy:
    roots: tuple[Path, ...]
    max_files: int = 20_000
    max_file_bytes: int = 1_000_000
    content_preview_chars: int = 4_000
    excludes: frozenset[str] = DEFAULT_EXCLUDES
    allow_content: bool = True
    time_budget_seconds: float | None = None


@dataclass(frozen=True, slots=True)
class FileCandidate:
    path: str
    size: int
    modified_at: str
    extension: str
    category: str
    fingerprint: str
    preview: str | None = None


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    scanned: int
    retained: int
    skipped: int
    errors: int
    roots: tuple[str, ...]


class SilentDiscovery:
    """Permission-gated bounded discovery; retains useful metadata, not filesystem noise."""

    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def run(self, policy: DiscoveryPolicy) -> DiscoveryReport:
        if not self._has_permission():
            raise PermissionError("discovery permission has not been granted")
        scanned = retained = skipped = errors = 0
        deadline = (
            time.monotonic() + policy.time_budget_seconds
            if policy.time_budget_seconds is not None
            else None
        )
        for path in self._walk(policy):
            if scanned >= policy.max_files or (
                deadline is not None and time.monotonic() >= deadline
            ):
                break
            scanned += 1
            try:
                candidate = self._candidate(path, policy)
                if candidate is None:
                    skipped += 1
                    continue
                retained += 1
                self.memory.set(
                    f"discovery.file.{candidate.fingerprint}",
                    asdict(candidate),
                    kind=MemoryKind.LEARNED,
                    confidence=0.7 if candidate.preview else 0.55,
                    source="silent-discovery",
                    evidence={"path": candidate.path, "modified_at": candidate.modified_at},
                )
            except (OSError, UnicodeError):
                errors += 1
        report = DiscoveryReport(
            scanned, retained, skipped, errors, tuple(str(root) for root in policy.roots)
        )
        self.memory.set(
            "discovery.last_report",
            asdict(report),
            kind=MemoryKind.TEMPORARY,
            source="silent-discovery",
            ttl_seconds=86_400,
        )
        return report

    def grant(self, roots: tuple[Path, ...]) -> None:
        normalized = tuple(str(path.expanduser().resolve()) for path in roots)
        self.memory.set(
            "permissions.discovery",
            {"granted": True, "roots": normalized, "at": datetime.now(UTC).isoformat()},
            kind=MemoryKind.CORE,
            protected=True,
            source="user-consent",
        )

    def _has_permission(self) -> bool:
        permission = self.memory.get("permissions.discovery")
        return bool(permission and permission.value.get("granted"))

    @staticmethod
    def _walk(policy: DiscoveryPolicy) -> Iterator[Path]:
        for root in policy.roots:
            root = root.expanduser().resolve()
            if not root.is_dir():
                continue
            for current, dirs, files in os.walk(root, followlinks=False):
                dirs[:] = [
                    name
                    for name in dirs
                    if name not in policy.excludes and not name.startswith(".")
                ]
                for name in files:
                    if name.startswith(".") or name in policy.excludes:
                        continue
                    yield Path(current) / name

    @staticmethod
    def _candidate(path: Path, policy: DiscoveryPolicy) -> FileCandidate | None:
        stat = path.stat()
        if not path.is_file() or stat.st_size > policy.max_file_bytes:
            return None
        category = SilentDiscovery._category(path)
        if category == "unknown":
            return None
        preview = None
        if policy.allow_content and path.suffix.lower() in TEXT_EXTENSIONS:
            preview = path.read_text(encoding="utf-8", errors="replace")[
                : policy.content_preview_chars
            ]
        identity = f"{path.resolve()}:{stat.st_size}:{stat.st_mtime_ns}"
        return FileCandidate(
            path=str(path.resolve()),
            size=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            extension=path.suffix.lower(),
            category=category,
            fingerprint=hashlib.sha256(identity.encode()).hexdigest()[:24],
            preview=preview,
        )

    @staticmethod
    def _category(path: Path) -> str:
        name = path.name
        if name in PROJECT_MARKERS or path.suffix.lower() in {".sln", ".csproj"}:
            return "project-marker"
        if path.suffix.lower() in TEXT_EXTENSIONS:
            return "text"
        if path.suffix.lower() in {".pdf", ".docx", ".xlsx", ".pptx"}:
            return "document"
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            return "image"
        return "unknown"
