from pathlib import Path

from neo.core.storage import resolve_data_location


def test_local_storage_created(tmp_path) -> None:
    target = tmp_path / "neo-data"
    location = resolve_data_location(target)
    assert location.path == target
    assert target.is_dir()
    assert location.removable is False


def test_read_only_storage_falls_back(monkeypatch, tmp_path) -> None:
    target = tmp_path / "blocked"
    real_touch = Path.touch

    def fail_probe(path: Path, *args, **kwargs):
        if path.name == ".neo-write-probe":
            raise OSError("read-only")
        return real_touch(path, *args, **kwargs)

    monkeypatch.setattr(Path, "touch", fail_probe)
    location = resolve_data_location(target)
    assert location.path != target
    assert location.path.is_dir()
    assert "read-only" in location.reason
