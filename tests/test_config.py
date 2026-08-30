from pathlib import Path

from neo.core.config import Settings


def test_settings_defaults(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.delenv("NEO_DATA_DIR", raising=False)
    settings = Settings.from_env(tmp_path / "missing.env")
    assert settings.data_dir == tmp_path / "neo"
    assert settings.main_model == "qwen3.5:9b"
    assert settings.light_model == "qwen3.5:0.8b"
