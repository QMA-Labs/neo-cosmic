from pathlib import Path

import pytest

from neo.discovery import DiscoveryPolicy, SilentDiscovery
from neo.memory import MemoryStore


def test_discovery_requires_permission_and_filters_noise(tmp_path: Path) -> None:
    root = tmp_path / "files"
    root.mkdir()
    (root / "notes.md").write_text("Important project note", encoding="utf-8")
    (root / "archive.bin").write_bytes(b"noise")
    ignored = root / "node_modules"
    ignored.mkdir()
    (ignored / "package.json").write_text("{}", encoding="utf-8")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    discovery = SilentDiscovery(store)
    with pytest.raises(PermissionError):
        discovery.run(DiscoveryPolicy((root,)))
    discovery.grant((root,))
    report = discovery.run(DiscoveryPolicy((root,)))
    assert report.retained == 1
    records = store.search("Important project note")
    assert records[0].value["category"] == "text"


def test_metadata_only_never_reads_preview(tmp_path: Path) -> None:
    root = tmp_path / "files"
    root.mkdir()
    (root / "secret.txt").write_text("private", encoding="utf-8")
    store = MemoryStore(tmp_path / "memory.sqlite3")
    discovery = SilentDiscovery(store)
    discovery.grant((root,))
    discovery.run(DiscoveryPolicy((root,), allow_content=False))
    entry = store.search("secret.txt")[0]
    assert entry.value["preview"] is None
