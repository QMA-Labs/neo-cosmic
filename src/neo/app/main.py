from __future__ import annotations

import os
import sys
import traceback

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication

from neo.app.window import PetWindow
from neo.bootstrap import bootstrap


class ErrorBridge(QObject):
    raised = Signal(str)


def main() -> int:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("NEO")
    app.setOrganizationName("NEO")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    runtime = bootstrap()
    window = PetWindow(runtime)
    error_bridge = ErrorBridge(window)
    error_bridge.raised.connect(window.recover_from_error)

    def report_error(exc_type, value, tb) -> None:
        traceback.print_exception(exc_type, value, tb)
        error_bridge.raised.emit(str(value) or exc_type.__name__)

    sys.excepthook = report_error
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
