import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from neo.app.pet_widget import PetWidget  # noqa: E402
from neo.app.state import PetState  # noqa: E402
from neo.app.window import PetWindow  # noqa: E402


def test_pet_state_transition() -> None:
    app = QApplication.instance() or QApplication([])
    pet = PetWidget()
    pet.set_state(PetState.THINKING)
    assert pet.state == PetState.THINKING
    pet.set_state(PetState.SUCCESS)
    assert pet.state == PetState.SUCCESS
    pet.close()
    app.processEvents()


def test_triple_click_signal_contract() -> None:
    app = QApplication.instance() or QApplication([])
    pet = PetWidget()
    requested = []
    pet.chat_requested.connect(lambda: requested.append(True))
    pet.show()
    for _ in range(3):
        QTest.mouseClick(pet, Qt.MouseButton.LeftButton, pos=QPoint(100, 100))
        app.processEvents()
    assert requested == [True]
    pet.close()
    app.processEvents()


def test_context_menu_contains_product_shortcuts() -> None:
    app = QApplication.instance() or QApplication([])
    pet = PetWidget()
    labels = [action.text() for action in pet.create_context_menu().actions()]
    assert any("بازکردن چت" in label for label in labels)
    assert any("GPU" in label for label in labels)
    assert any("تحلیل صفحه" in label for label in labels)
    assert any("تست NEO" in label for label in labels)
    assert any("حرکت خودکار" in label for label in labels)
    assert any("روشن/تیره" in label for label in labels)
    pet.close()
    app.processEvents()


def test_screen_intent_detection() -> None:
    assert PetWindow._asks_about_screen("این کد روی صفحه من چرا خطا دارد؟")
    assert PetWindow._asks_about_screen("look at my screen")
    assert not PetWindow._asks_about_screen("سلام NEO")


def test_local_intents_do_not_need_llm() -> None:
    assert PetWindow._asks_for_metrics("الان گرافیک رو بده")
    assert PetWindow._asks_for_identity("من کیم")
    assert PetWindow._asks_for_files("فایل پروژه را پیدا کن")
    assert not PetWindow._asks_for_files("فایل چیست؟")
    assert PetWindow._asks_for_battery("لپ‌تاپم چند درصد شارژ داره؟")
    assert PetWindow._asks_capabilities("چه کارهایی میتونی انجام بدی؟")


def test_animation_clock_advances() -> None:
    app = QApplication.instance() or QApplication([])
    pet = PetWidget()
    before = pet._phase
    pet._tick()
    assert pet._phase != before
    pet.close()
    app.processEvents()


def test_speech_overlay_stays_above_3d_view() -> None:
    app = QApplication.instance() or QApplication([])
    pet = PetWidget()
    pet.speak("Hello")
    assert pet._speech_overlay.isVisibleTo(pet)
    assert pet._speech_overlay.text() == "Hello"
    pet._clear_speech()
    assert pet._speech_overlay.isHidden()
    pet.close()
    app.processEvents()
