import sqlite3

from neo.memory import MemoryStore


def test_phase_one_database_migrates_without_data_loss(tmp_path) -> None:
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        """CREATE TABLE memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL)"""
    )
    connection.execute(
        "INSERT INTO memories(key,value_json,created_at,updated_at) VALUES(?,?,?,?)",
        ("legacy", '"safe"', "2026-01-01", "2026-01-01"),
    )
    connection.commit()
    connection.close()
    store = MemoryStore(database)
    entry = store.get("legacy")
    assert entry is not None
    assert entry.value == "safe"
    assert entry.kind == "learned"
