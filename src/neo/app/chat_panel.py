from __future__ import annotations

import html

from PySide6.QtCore import QElapsedTimer, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from neo.app.theme import LIGHT_PANEL_STYLE, PANEL_STYLE
from neo.device.profile import MachineProfile


class ChatTranscript(QTextBrowser):
    def __init__(self) -> None:
        super().__init__()
        self.setOpenExternalLinks(True)
        self.setObjectName("transcript")
        self.setMinimumHeight(300)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.document().setDefaultStyleSheet(
            "body{font-family:'Vazirmatn','Noto Sans Arabic','Sans';font-size:13px;}"
        )

    def setText(self, text: str) -> None:  # noqa: N802
        self.append_message("NEO", text, assistant=True)

    def append_message(self, sender: str, text: str, *, assistant: bool) -> None:
        color = "#8AF7D8" if assistant else "#D2DBFF"
        background = "rgba(29,45,65,0.78)" if assistant else "rgba(77,71,140,0.72)"
        alignment = "left" if assistant else "right"
        direction = "rtl"
        safe = html.escape(text).replace("\n", "<br>")
        self.append(
            f'<p dir="{direction}" align="{alignment}" style="margin:8px 3px;">'
            f'<span style="background:{background};color:#F4F7FF;padding:10px;">'
            f'<b style="color:{color}">{html.escape(sender)}</b><br>{safe}</span></p>'
        )
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())


class ChatPanel(QFrame):
    submitted = Signal(str)
    quick_requested = Signal(str)
    cancel_requested = Signal()
    control_requested = Signal()
    mode_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("glassPanel")
        self.setFixedWidth(430)
        self.setStyleSheet(PANEL_STYLE)
        self._light_theme = False
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(44)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(47, 97, 180, 115))
        self.setGraphicsEffect(shadow)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        header = QHBoxLayout()
        title = QLabel("N E O")
        title.setStyleSheet("font-size: 22px; font-weight: 900; letter-spacing: 4px")
        self.gpu_badge = QLabel("GPU --")
        self.gpu_badge.setObjectName("gpuBadge")
        self.connection_badge = QLabel("LOCAL")
        self.connection_badge.setObjectName("connectionBadge")
        controls = QPushButton("⌘")
        controls.setObjectName("controlButton")
        controls.setToolTip("مرکز کنترل NEO")
        controls.setFixedWidth(36)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.connection_badge)
        header.addWidget(self.gpu_badge)
        header.addWidget(controls)
        self.status = QLabel("آماده‌ام")
        self.status.setObjectName("muted")
        self.activity = QLabel("سیستم محلی آماده است")
        self.activity.setObjectName("activity")
        self.activity.setWordWrap(True)
        self.message = ChatTranscript()
        self.message.setText("سلام؛ من NEO هستم. هر وقت خواستی اینجا هستم.")
        self.metrics = QLabel("CPU --  •  RAM --  •  NET --")
        self.metrics.setObjectName("muted")
        self.metrics.setWordWrap(True)
        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("با NEO حرف بزن…")
        send = QPushButton("➤")
        send.setFixedWidth(48)
        self.send = send
        self._busy = False
        self._elapsed_clock = QElapsedTimer()
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(250)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        row.addWidget(self.input, 1)
        row.addWidget(send)
        layout.addLayout(header)
        layout.addWidget(self.status)
        layout.addWidget(self.activity)
        self.mode_selector = QComboBox()
        self.mode_selector.setObjectName("modeSelector")
        layout.addWidget(self.mode_selector)
        self.elapsed = QLabel("00:00")
        self.elapsed.setObjectName("elapsed")
        self.elapsed.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.elapsed)
        layout.addWidget(self.metrics)
        layout.addWidget(self.message, 1)
        quick = QHBoxLayout()
        for title, command in (
            ("GPU", "الان گرافیک رو بده"),
            ("فایل‌ها", "فایل‌های مرتبط را پیدا کن"),
            ("صفحه", "صفحهٔ فعلی من را تحلیل کن"),
            ("حافظه", "درباره من چی میدونی"),
        ):
            button = QPushButton(title)
            button.setObjectName("chip")
            button.clicked.connect(
                lambda _checked=False, value=command: self.quick_requested.emit(value)
            )
            quick.addWidget(button)
        layout.addLayout(quick)
        layout.addLayout(row)
        send.clicked.connect(self._send_or_cancel)
        controls.clicked.connect(self.control_requested.emit)
        self.input.returnPressed.connect(self._submit)
        self.mode_selector.currentIndexChanged.connect(self._emit_mode)

    def set_chat_modes(self, modes: tuple[tuple[str, str], ...], current: str) -> None:
        self.mode_selector.blockSignals(True)
        self.mode_selector.clear()
        for key, title in modes:
            self.mode_selector.addItem(title, key)
        index = self.mode_selector.findData(current)
        self.mode_selector.setCurrentIndex(max(0, index))
        self.mode_selector.blockSignals(False)

    def _emit_mode(self, index: int) -> None:
        if index >= 0:
            self.mode_changed.emit(str(self.mode_selector.itemData(index)))

    def apply_language(self, language: str) -> None:
        english = language == "en"
        direction = (
            Qt.LayoutDirection.LeftToRight if english else Qt.LayoutDirection.RightToLeft
        )
        self.setLayoutDirection(direction)
        self.message.setLayoutDirection(direction)
        self.status.setText("Ready" if english else "آماده‌ام")
        self.activity.setText(
            "Local system ready" if english else "سیستم محلی آماده است"
        )
        self.input.setPlaceholderText(
            "Talk to NEO…" if english else "با NEO حرف بزن…"
        )

    def set_activity(self, text: str, *, error: bool = False) -> None:
        """Show transient product state without polluting the conversation."""
        self.activity.setText(text)
        self.activity.setProperty("error", error)
        self.activity.style().unpolish(self.activity)
        self.activity.style().polish(self.activity)

    def set_connection(self, *, online: bool, model: str) -> None:
        short_model = model.split(":", 1)[-1].upper()
        self.connection_badge.setText(f"{'WEB' if online else 'LOCAL'} · {short_model}")
        self.connection_badge.setProperty("online", online)
        self.connection_badge.style().unpolish(self.connection_badge)
        self.connection_badge.style().polish(self.connection_badge)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.input.setEnabled(not busy)
        self.send.setEnabled(True)
        self.send.setText("■" if busy else "➤")
        self.send.setToolTip("توقف پاسخ" if busy else "ارسال")
        if busy:
            self._elapsed_clock.restart()
            self._elapsed_timer.start()
            self._update_elapsed()
        else:
            self._elapsed_timer.stop()

    def _update_elapsed(self) -> None:
        seconds = max(0, self._elapsed_clock.elapsed() // 1000)
        self.elapsed.setText(f"{seconds // 60:02d}:{seconds % 60:02d}")

    def _send_or_cancel(self) -> None:
        if self._busy:
            self.cancel_requested.emit()
        else:
            self._submit()

    def append_user(self, text: str) -> None:
        self.message.append_message("تو", text, assistant=False)

    def _submit(self) -> None:
        text = self.input.text().strip()
        if text:
            self.input.clear()
            self.append_user(text)
            self.submitted.emit(text)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 28, 28)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        if self._light_theme:
            gradient.setColorAt(0, QColor(255, 255, 255, 242))
            gradient.setColorAt(0.48, QColor(229, 239, 252, 235))
            gradient.setColorAt(1, QColor(220, 247, 241, 236))
        else:
            gradient.setColorAt(0, QColor(38, 48, 78, 230))
            gradient.setColorAt(0.48, QColor(15, 23, 42, 218))
            gradient.setColorAt(1, QColor(22, 55, 67, 225))
        painter.fillPath(path, gradient)
        painter.setPen(QColor(201, 229, 255, 72))
        painter.drawPath(path)
        super().paintEvent(event)

    def apply_theme(self, light: bool) -> None:
        self._light_theme = light
        self.setStyleSheet(LIGHT_PANEL_STYLE if light else PANEL_STYLE)
        self.update()

    def show_profile(self, profile: MachineProfile, model: str) -> None:
        gpu = profile.hardware.gpu_name or "بدون GPU مجزا"
        self.message.setText(
            f"{profile.manufacturer or ''} {profile.model or profile.hostname}\n"
            f"{profile.operating_system}\nCPU: {profile.cpu_model}\nGPU: {gpu}\n"
            f"RAM: {profile.hardware.ram_total_gb:.1f} GB\nمدل فعال: {model}"
        )
