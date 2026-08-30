import pytest

from neo.memory import MemoryStore
from neo.screen import ScreenIntelligence


def test_screen_requires_consent(tmp_path) -> None:
    screen = ScreenIntelligence(MemoryStore(tmp_path / "memory.sqlite3"))
    with pytest.raises(PermissionError):
        screen.capture()


def test_app_categories() -> None:
    assert ScreenIntelligence._categorize("Visual Studio Code") == "code"
    assert ScreenIntelligence._categorize("Adobe Premiere Pro") == "creative"
    assert ScreenIntelligence._categorize("Google Chrome") == "browser"
    assert ScreenIntelligence._categorize("Password Manager") == "unknown"


def test_screen_grant_and_revoke(tmp_path) -> None:
    store = MemoryStore(tmp_path / "memory.sqlite3")
    screen = ScreenIntelligence(store)
    screen.grant()
    assert store.get("permissions.screen_capture").value is True  # type: ignore[union-attr]
    screen.revoke()
    assert store.get("permissions.screen_capture").value is False  # type: ignore[union-attr]
