from concurrent.futures import ThreadPoolExecutor

from neo.memory import MemoryStore


def test_memory_round_trip_and_update(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    first = store.set("profile", {"name": "NEO", "active": True})
    assert first.value["name"] == "NEO"
    updated = store.set("profile", [1, 2, 3])
    assert updated.id == first.id
    assert store.get("profile").value == [1, 2, 3]  # type: ignore[union-attr]
    assert len(store.list()) == 1
    assert store.delete("profile") is True
    assert store.get("profile") is None


def test_memory_rejects_empty_key(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    try:
        store.set(" ", "value")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_memory_serializes_concurrent_background_writes(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")

    def write(index: int) -> None:
        store.set(f"file.{index}", {"index": index})

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(write, range(120)))
    assert len(store.list(200)) == 120
