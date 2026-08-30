from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any


class MemoryKind(StrEnum):
    CORE = "core"
    LEARNED = "learned"
    TEMPORARY = "temporary"


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    id: int
    key: str
    value: Any
    created_at: str
    updated_at: str
    kind: str = MemoryKind.LEARNED
    confidence: float = 1.0
    protected: bool = False
    source: str | None = None
    evidence: Any = None
    expires_at: str | None = None
    access_count: int = 0


@dataclass(frozen=True, slots=True)
class MemoryRelation:
    id: int
    source_key: str
    relation: str
    target_key: str
    confidence: float
    evidence: Any
    created_at: str


class MemoryStore:
    def __init__(self, database: Path) -> None:
        self.database = database
        self._lock = threading.RLock()
        database.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    def _initialize(self) -> None:
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT NOT NULL UNIQUE,
                    value_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'learned', confidence REAL NOT NULL DEFAULT 1.0,
                    protected INTEGER NOT NULL DEFAULT 0, source TEXT, evidence_json TEXT,
                    expires_at TEXT, access_count INTEGER NOT NULL DEFAULT 0, last_accessed TEXT
                )"""
            )
            self._migrate_columns(connection)
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memory_relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, source_key TEXT NOT NULL,
                    relation TEXT NOT NULL, target_key TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 1.0, evidence_json TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(source_key, relation, target_key),
                    FOREIGN KEY(source_key) REFERENCES memories(key) ON DELETE CASCADE,
                    FOREIGN KEY(target_key) REFERENCES memories(key) ON DELETE CASCADE)"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memory_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, memory_key TEXT NOT NULL,
                    action TEXT NOT NULL, snapshot_json TEXT, occurred_at TEXT NOT NULL)"""
            )
            connection.execute("CREATE INDEX IF NOT EXISTS idx_memory_kind ON memories(kind)")

    @staticmethod
    def _migrate_columns(connection: sqlite3.Connection) -> None:
        existing = {row[1] for row in connection.execute("PRAGMA table_info(memories)")}
        additions = {
            "kind": "TEXT NOT NULL DEFAULT 'learned'",
            "confidence": "REAL NOT NULL DEFAULT 1.0",
            "protected": "INTEGER NOT NULL DEFAULT 0",
            "source": "TEXT",
            "evidence_json": "TEXT",
            "expires_at": "TEXT",
            "access_count": "INTEGER NOT NULL DEFAULT 0",
            "last_accessed": "TEXT",
        }
        for name, definition in additions.items():
            if name not in existing:
                connection.execute(f"ALTER TABLE memories ADD COLUMN {name} {definition}")

    def set(
        self,
        key: str,
        value: Any,
        *,
        kind: MemoryKind | str = MemoryKind.LEARNED,
        confidence: float = 1.0,
        protected: bool = False,
        source: str | None = None,
        evidence: Any = None,
        ttl_seconds: int | None = None,
    ) -> MemoryEntry:
        if not key.strip():
            raise ValueError("memory key must not be empty")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        kind = MemoryKind(kind)
        if kind == MemoryKind.TEMPORARY and ttl_seconds is None:
            ttl_seconds = 3600
        now = datetime.now(UTC)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        evidence_json = json.dumps(evidence, ensure_ascii=False) if evidence is not None else None
        with self._lock, closing(self._connect()) as connection, connection:
            old = connection.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
            if old:
                self._history(connection, key, "update", dict(old))
            connection.execute(
                """INSERT INTO memories(key,value_json,created_at,updated_at,kind,confidence,
                       protected,source,evidence_json,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,
                       updated_at=excluded.updated_at,kind=excluded.kind,
                       confidence=excluded.confidence,protected=MAX(memories.protected,excluded.protected),
                       source=excluded.source,evidence_json=excluded.evidence_json,
                       expires_at=excluded.expires_at""",
                (
                    key,
                    encoded,
                    now.isoformat(),
                    now.isoformat(),
                    kind.value,
                    confidence,
                    int(protected),
                    source,
                    evidence_json,
                    expires_at,
                ),
            )
            row = connection.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
        assert row is not None
        return self._from_row(row)

    def get(self, key: str) -> MemoryEntry | None:
        self.purge_expired()
        with self._lock, closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
            if row:
                connection.execute(
                    "UPDATE memories SET access_count=access_count+1,last_accessed=? WHERE key=?",
                    (datetime.now(UTC).isoformat(), key),
                )
        return self._from_row(row) if row else None

    def forget(self, key: str, *, force: bool = False) -> bool:
        with self._lock, closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT * FROM memories WHERE key=?", (key,)).fetchone()
            if not row:
                return False
            if row["protected"] and not force:
                raise PermissionError("protected memory requires force=True to forget")
            self._history(connection, key, "forget", dict(row))
            connection.execute("DELETE FROM memories WHERE key=?", (key,))
            return True

    def delete(self, key: str) -> bool:
        return self.forget(key)

    def list(self, limit: int = 100, *, kind: MemoryKind | str | None = None) -> list[MemoryEntry]:
        self.purge_expired()
        query, params = "SELECT * FROM memories", []
        if kind is not None:
            query += " WHERE kind=?"
            params.append(MemoryKind(kind).value)
        query += " ORDER BY protected DESC,updated_at DESC LIMIT ?"
        params.append(max(1, limit))
        with self._lock, closing(self._connect()) as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._from_row(row) for row in rows]

    def search(self, query: str, limit: int = 20) -> list[MemoryEntry]:
        self.purge_expired()
        term = f"%{query.casefold()}%"
        with self._lock, closing(self._connect()) as connection:
            rows = connection.execute(
                """SELECT * FROM memories WHERE lower(key) LIKE ? OR lower(value_json) LIKE ?
                   OR lower(COALESCE(source,'')) LIKE ?
                   ORDER BY protected DESC,confidence DESC,updated_at DESC LIMIT ?""",
                (term, term, term, max(1, limit)),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def relate(
        self,
        source_key: str,
        relation: str,
        target_key: str,
        *,
        confidence: float = 1.0,
        evidence: Any = None,
    ) -> MemoryRelation:
        if not relation.strip() or not 0 <= confidence <= 1:
            raise ValueError("invalid relation or confidence")
        now = datetime.now(UTC).isoformat()
        encoded = json.dumps(evidence, ensure_ascii=False) if evidence is not None else None
        with self._lock, closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO memory_relations(source_key,relation,target_key,confidence,
                       evidence_json,created_at) VALUES(?,?,?,?,?,?)
                   ON CONFLICT(source_key,relation,target_key) DO UPDATE SET
                       confidence=excluded.confidence,evidence_json=excluded.evidence_json""",
                (source_key, relation, target_key, confidence, encoded, now),
            )
            row = connection.execute(
                "SELECT * FROM memory_relations WHERE source_key=? AND relation=? AND target_key=?",
                (source_key, relation, target_key),
            ).fetchone()
        assert row is not None
        return self._relation_from_row(row)

    def relations(self, key: str) -> list[MemoryRelation]:
        with self._lock, closing(self._connect()) as connection:
            rows = connection.execute(
                """SELECT * FROM memory_relations WHERE source_key=? OR target_key=?
                   ORDER BY confidence DESC""",
                (key, key),
            ).fetchall()
        return [self._relation_from_row(row) for row in rows]

    def purge_expired(self) -> int:
        with self._lock, closing(self._connect()) as connection, connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at<=?",
                (datetime.now(UTC).isoformat(),),
            )
            return cursor.rowcount

    @staticmethod
    def _history(
        connection: sqlite3.Connection, key: str, action: str, snapshot: dict[str, Any]
    ) -> None:
        connection.execute(
            """INSERT INTO memory_history(memory_key,action,snapshot_json,occurred_at)
               VALUES(?,?,?,?)""",
            (key, action, json.dumps(snapshot, ensure_ascii=False), datetime.now(UTC).isoformat()),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            row["id"],
            row["key"],
            json.loads(row["value_json"]),
            row["created_at"],
            row["updated_at"],
            row["kind"],
            float(row["confidence"]),
            bool(row["protected"]),
            row["source"],
            json.loads(row["evidence_json"]) if row["evidence_json"] else None,
            row["expires_at"],
            int(row["access_count"]),
        )

    @staticmethod
    def _relation_from_row(row: sqlite3.Row) -> MemoryRelation:
        return MemoryRelation(
            row["id"],
            row["source_key"],
            row["relation"],
            row["target_key"],
            float(row["confidence"]),
            json.loads(row["evidence_json"]) if row["evidence_json"] else None,
            row["created_at"],
        )
