from neo.intelligence.chat_modes import CHAT_MODES, get_chat_mode


def test_specialist_modes_are_unique_and_retrievable() -> None:
    keys = [mode.key for mode in CHAT_MODES]
    assert len(keys) == len(set(keys))
    assert {"companion", "expert", "coder", "philosopher", "researcher"} <= set(keys)
    assert get_chat_mode("coder").key == "coder"
    assert get_chat_mode("missing").key == "companion"


def test_only_research_mode_requires_web_by_default() -> None:
    web_modes = [mode.key for mode in CHAT_MODES if mode.uses_web]
    assert web_modes == ["researcher"]
