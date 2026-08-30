from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import QLabel, QMenu, QWidget

from neo.app.state import PetState


class PetWidget(QWidget):
    clicked = Signal()
    chat_requested = Signal()
    profile_requested = Signal()
    metrics_requested = Signal()
    screen_requested = Signal()
    self_test_requested = Signal()
    roam_toggled = Signal()
    theme_toggled = Signal()
    quit_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(210, 224)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._speech_overlay = QLabel(self)
        self._speech_overlay.setGeometry(4, 2, 202, 42)
        self._speech_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._speech_overlay.setWordWrap(True)
        self._speech_overlay.setStyleSheet(
            "background: rgba(10,18,31,235); color: #F4F7FF; "
            "border: 1px solid #8AA8FF; border-radius: 14px; padding: 4px;"
        )
        self._speech_overlay.hide()
        self._state = PetState.IDLE
        self._phase = 0.0
        self._drag_origin: QPoint | None = None
        self._window_origin: QPoint | None = None
        self._moved = False
        self._system_move_started = False
        self._click_count = 0
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.setInterval(450)
        self._click_timer.timeout.connect(self._finish_clicks)
        asset = Path(__file__).with_name("assets") / "neo-cosmic-v1.png"
        self._pet_image = QPixmap(str(asset))
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)
        self._speech = ""
        self._speech_timer = QTimer(self)
        self._speech_timer.setSingleShot(True)
        self._speech_timer.timeout.connect(self._clear_speech)

    @property
    def state(self) -> PetState:
        return self._state

    def set_state(self, state: PetState) -> None:
        self._state = state
        self.update()

    def _tick(self) -> None:
        self._phase = (self._phase + 0.08) % (math.tau)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bob = math.sin(self._phase * (2 if self._state == PetState.WALKING else 1)) * 3
        painter.translate(0, bob)
        if not self._pet_image.isNull():
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            pulse = 1.0 + math.sin(self._phase) * 0.018
            tilt = math.sin(self._phase * 0.65) * (2.5 if self._state == PetState.IDLE else 5.0)
            if self._state == PetState.THINKING:
                pulse += math.sin(self._phase * 2) * 0.025
            painter.save()
            painter.translate(105, 112)
            painter.rotate(tilt)
            painter.scale(pulse, pulse)
            painter.translate(-105, -112)
            painter.drawPixmap(5, 2, 200, 220, self._pet_image)
            painter.restore()
            self._paint_badge(painter)
            self._paint_speech(painter)
            return
        center = QPointF(86, 88)

        glow = QLinearGradient(25, 25, 145, 145)
        glow.setColorAt(0, QColor("#8AA8FF"))
        glow.setColorAt(1, QColor("#71E5C1"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(113, 229, 193, 25))
        painter.drawEllipse(center, 72, 72)

        body = QPainterPath()
        body.addRoundedRect(QRectF(34, 38, 104, 112), 48, 48)
        painter.setBrush(glow)
        painter.drawPath(body)
        painter.setBrush(QColor("#111827"))
        painter.drawRoundedRect(QRectF(46, 53, 80, 62), 27, 27)

        blink = self._state == PetState.SLEEPING or (
            self._phase > 5.8 and self._state == PetState.IDLE
        )
        eye_pen = QPen(QColor("#E9FFF9"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(eye_pen)
        if blink:
            painter.drawLine(QPointF(65, 82), QPointF(75, 82))
            painter.drawLine(QPointF(97, 82), QPointF(107, 82))
        else:
            pupil_shift = math.sin(self._phase / 2) * 2
            painter.drawPoint(QPointF(70 + pupil_shift, 80))
            painter.drawPoint(QPointF(102 + pupil_shift, 80))
        painter.setPen(QPen(QColor("#71E5C1"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(QRectF(76, 83, 20, 15), 200 * 16, 140 * 16)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#111827"))
        foot = math.sin(self._phase * 3) * 5 if self._state == PetState.WALKING else 0
        painter.drawRoundedRect(QRectF(48 + foot, 140, 31, 13), 6, 6)
        painter.drawRoundedRect(QRectF(93 - foot, 140, 31, 13), 6, 6)
        self._paint_badge(painter)
        self._paint_speech(painter)

    def speak(self, text: str, duration_ms: int = 5500) -> None:
        self._speech = text
        self._speech_overlay.setText(text)
        self._speech_overlay.show()
        self._speech_overlay.raise_()
        self._speech_timer.start(duration_ms)
        self.update()

    def _clear_speech(self) -> None:
        self._speech = ""
        self._speech_overlay.hide()
        self.update()

    def _paint_speech(self, painter: QPainter) -> None:
        if not self._speech:
            return
        painter.resetTransform()
        bubble = QRectF(4, 2, 202, 42)
        painter.setBrush(QColor(10, 18, 31, 235))
        painter.setPen(QPen(QColor("#8AA8FF"), 1.5))
        painter.drawRoundedRect(bubble, 14, 14)
        painter.setPen(QColor("#F4F7FF"))
        painter.drawText(
            bubble.adjusted(8, 4, -8, -4), Qt.AlignmentFlag.AlignCenter, self._speech
        )

    def _paint_badge(self, painter: QPainter) -> None:
        if self._state not in {PetState.THINKING, PetState.LOADING, PetState.SUCCESS}:
            return
        painter.setBrush(QColor("#111827"))
        painter.setPen(QPen(QColor("#71E5C1"), 2))
        painter.drawEllipse(QPointF(136, 38), 17, 17)
        painter.setPen(QColor("#F4F7FF"))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(14)
        painter.setFont(font)
        symbol = "✓" if self._state == PetState.SUCCESS else "◌"
        painter.drawText(QRectF(119, 21, 34, 34), Qt.AlignmentFlag.AlignCenter, symbol)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.globalPosition().toPoint()
            self._window_origin = self.window().pos()
            self._moved = False
            self._system_move_started = False

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_origin is not None and self._window_origin is not None:
            delta = event.globalPosition().toPoint() - self._drag_origin
            if delta.manhattanLength() > 4:
                self._moved = True
                handle = self.window().windowHandle()
                if handle is not None and not self._system_move_started:
                    self._system_move_started = bool(handle.startSystemMove())
            if not self._system_move_started:
                self.window().move(self._window_origin + delta)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._window_origin is not None:
            moved_by_system = (self.window().pos() - self._window_origin).manhattanLength() > 4
            self._moved = self._moved or moved_by_system
        if event.button() == Qt.MouseButton.LeftButton and not self._moved:
            self._click_count += 1
            if self._click_count >= 3:
                self._click_timer.stop()
                self._click_count = 0
                self.chat_requested.emit()
            else:
                self._click_timer.start()
        self._drag_origin = None
        self._window_origin = None
        self._system_move_started = False

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = self.create_context_menu()
        menu.exec(event.globalPos())

    def create_context_menu(self) -> QMenu:
        menu = QMenu(self)
        menu.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        menu.addAction("‏💬 بازکردن چت", self.chat_requested.emit)
        menu.addSeparator()
        menu.addAction("‏💻 مشخصات کامل دستگاه", self.profile_requested.emit)
        menu.addAction("‏📊 CPU، RAM، GPU و شبکه", self.metrics_requested.emit)
        menu.addAction("‏👁 تحلیل صفحهٔ فعلی", self.screen_requested.emit)
        menu.addAction("‏🧪 اجرای تست NEO", self.self_test_requested.emit)
        menu.addAction("‏🚀 روشن/خاموش‌کردن حرکت خودکار", self.roam_toggled.emit)
        menu.addAction("‏◐ تغییر حالت روشن/تیره", self.theme_toggled.emit)
        menu.addSeparator()
        menu.addAction("‏✕ خروج", self.quit_requested.emit)
        return menu

    def _finish_clicks(self) -> None:
        if self._click_count:
            self.clicked.emit()
        self._click_count = 0
