import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEventLoop, QThreadPool, QTimer  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from neo.app.background import BackgroundWorker  # noqa: E402


def test_background_worker_keeps_ui_event_loop_responsive() -> None:
    app = QApplication.instance() or QApplication([])
    loop = QEventLoop()
    worker = BackgroundWorker(lambda: (time.sleep(0.05), "done")[1])
    results: list[str] = []
    ui_ticks: list[bool] = []
    worker.signals.result.connect(results.append)
    worker.signals.finished.connect(loop.quit)
    QTimer.singleShot(5, lambda: ui_ticks.append(True))
    QThreadPool.globalInstance().start(worker)
    loop.exec()
    assert results == ["done"]
    assert ui_ticks == [True]
    app.processEvents()
