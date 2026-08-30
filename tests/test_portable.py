from pathlib import Path

from neo.core.portable import configure_portable_environment, detect_portable_layout


def test_portable_layout_uses_marker_not_drive_letter(tmp_path, monkeypatch) -> None:
    root = tmp_path / "NEO-DRIVE"
    nested = root / "app" / "runtime"
    nested.mkdir(parents=True)
    (root / "NEO_PORTABLE").touch()
    layout = detect_portable_layout(nested)
    assert layout.enabled and layout.root == root
    monkeypatch.delenv("NEO_DATA_DIR", raising=False)
    monkeypatch.delenv("OLLAMA_MODELS", raising=False)
    configure_portable_environment(layout)
    assert Path(layout.data).is_dir()  # type: ignore[arg-type]
    assert Path(layout.models).is_dir()  # type: ignore[arg-type]


def test_local_mode_without_marker(tmp_path) -> None:
    layout = detect_portable_layout(tmp_path)
    assert layout.enabled is False
