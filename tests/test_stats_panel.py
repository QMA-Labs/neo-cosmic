import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from neo.app.metrics import LiveMetrics  # noqa: E402
from neo.app.stats_panel import LiveStatsPanel  # noqa: E402


def test_stats_panel_displays_gpu_and_vram_separately() -> None:
    app = QApplication.instance() or QApplication([])
    panel = LiveStatsPanel()
    panel.update_metrics(LiveMetrics(20, 40, 6, 30, 100, 1, 0.5, 80, True, 25, 7, 8, 60, 45))
    assert panel.rows["gpu"][1].text() == "25%"
    assert panel.rows["vram"][1].text() == "7.0/8.0G"
    panel.close()
    app.processEvents()
