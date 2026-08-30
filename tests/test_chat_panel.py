import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from neo.app.chat_panel import ChatPanel  # noqa: E402


def test_chat_transcript_appends_instead_of_replacing() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    panel.message.setText("پاسخ اول")
    panel.message.setText("پاسخ دوم")
    transcript = panel.message.toPlainText()
    assert "|" not in transcript
    assert "پاسخ اول" in transcript
    assert "پاسخ دوم" in transcript
    panel.close()
    app.processEvents()


def test_chat_transcript_keeps_question_when_error_is_appended() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    panel.append_user("سؤال من")
    panel.message.setText("اتصال مدل موقتاً برقرار نشد")
    transcript = panel.message.toPlainText()
    assert "سؤال من" in transcript
    assert "اتصال مدل" in transcript
    panel.close()
    app.processEvents()


def test_persian_chat_is_right_to_left_and_has_quick_actions() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    assert panel.layoutDirection().name == "RightToLeft"
    assert panel.message.layoutDirection().name == "RightToLeft"
    chips = [button.text() for button in panel.findChildren(type(panel.send))]
    assert "GPU" in chips
    assert "حافظه" in chips
    panel.close()
    app.processEvents()


def test_light_and_dark_theme_switch() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    panel.apply_theme(True)
    assert panel._light_theme is True
    panel.apply_theme(False)
    assert panel._light_theme is False
    panel.close()
    app.processEvents()


def test_busy_send_button_becomes_stop_control() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    cancelled = []
    panel.cancel_requested.connect(lambda: cancelled.append(True))
    panel.set_busy(True)
    assert panel.send.text() == "■"
    panel.send.click()
    assert cancelled == [True]
    panel.close()
    app.processEvents()


def test_activity_does_not_pollute_conversation_and_connection_is_clear() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    before = panel.message.toPlainText()
    panel.set_activity("در حال بررسی مدل…")
    panel.set_connection(online=True, model="qwen3.5:9b")
    assert panel.message.toPlainText() == before
    assert panel.activity.text() == "در حال بررسی مدل…"
    assert panel.connection_badge.text() == "WEB · 9B"
    panel.close()
    app.processEvents()


def test_chat_mode_selector_emits_stable_key() -> None:
    app = QApplication.instance() or QApplication([])
    panel = ChatPanel()
    selected = []
    panel.mode_changed.connect(selected.append)
    panel.set_chat_modes((("companion", "همراه"), ("coder", "برنامه‌نویس")), "companion")
    panel.mode_selector.setCurrentIndex(1)
    assert selected == ["coder"]
    panel.close()
    app.processEvents()
