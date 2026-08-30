from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar, QVBoxLayout

from neo.app.metrics import LiveMetrics
from neo.app.theme import LIGHT_PANEL_STYLE, PANEL_STYLE


class LiveStatsPanel(QFrame):
    close_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("panel")
        self.setFixedWidth(250)
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        header = QGridLayout()
        title = QLabel("NEO SYSTEM PULSE")
        title.setStyleSheet("font-weight: 800; color: #71E5C1")
        close = QLabel("✕")
        close.setToolTip("بستن آمار")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.mousePressEvent = lambda _event: self.close_requested.emit()
        header.addWidget(title, 0, 0)
        header.addWidget(close, 0, 1)
        layout.addLayout(header)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)
        self.rows: dict[str, tuple[QProgressBar, QLabel]] = {}
        for row, (key, label) in enumerate(
            (("cpu", "CPU"), ("gpu", "GPU"), ("ram", "RAM"), ("vram", "VRAM"), ("disk", "DISK"))
        ):
            name = QLabel(label)
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setTextVisible(False)
            bar.setFixedHeight(8)
            value = QLabel("--")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            grid.addWidget(name, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(value, row, 2)
            self.rows[key] = bar, value
        layout.addLayout(grid)
        self.details = QLabel("TEMP --  •  POWER --\nNET ↓-- ↑--  •  BAT --")
        self.details.setObjectName("muted")
        self.details.setWordWrap(True)
        layout.addWidget(self.details)

    def update_metrics(self, metrics: LiveMetrics) -> None:
        self._set("cpu", metrics.cpu_percent, f"{metrics.cpu_percent:.0f}%")
        self._set("ram", metrics.ram_percent, f"{metrics.ram_percent:.0f}%")
        self._set("disk", metrics.storage_percent, f"{metrics.storage_percent:.0f}%")
        self._set("gpu", metrics.gpu_percent, self._percent(metrics.gpu_percent))
        vram_percent = None
        if metrics.vram_used_gb is not None and metrics.vram_total_gb:
            vram_percent = metrics.vram_used_gb / metrics.vram_total_gb * 100
            vram_text = f"{metrics.vram_used_gb:.1f}/{metrics.vram_total_gb:.1f}G"
        else:
            vram_text = "--"
        self._set("vram", vram_percent, vram_text)
        temperature = (
            f"{metrics.gpu_temperature_c:.0f}°C"
            if metrics.gpu_temperature_c is not None
            else "--"
        )
        power = f"{metrics.gpu_power_w:.0f}W" if metrics.gpu_power_w is not None else "--"
        battery = f"{metrics.battery_percent:.0f}%" if metrics.battery_percent is not None else "--"
        self.details.setText(
            f"TEMP {temperature}  •  POWER {power}\n"
            f"NET ↓{metrics.network_down_mbps:.2f} ↑{metrics.network_up_mbps:.2f} Mbps"
            f"  •  BAT {battery}"
        )

    def apply_theme(self, light: bool) -> None:
        self.setStyleSheet(LIGHT_PANEL_STYLE if light else PANEL_STYLE)

    def _set(self, key: str, percent: float | None, text: str) -> None:
        bar, value = self.rows[key]
        bar.setValue(round(percent or 0))
        bar.setEnabled(percent is not None)
        value.setText(text)

    @staticmethod
    def _percent(value: float | None) -> str:
        return f"{value:.0f}%" if value is not None else "--"
