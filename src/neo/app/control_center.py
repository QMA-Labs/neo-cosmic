from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class ControlCenter(QDialog):
    """Small, understandable control surface for the companion's persistent choices."""

    def __init__(
        self,
        parent,
        *,
        owner_name: str,
        model: str,
        data_path: str,
        roaming: bool,
        light_theme: bool,
        web_enabled: bool,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("مرکز کنترل NEO")
        self.setMinimumWidth(430)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout(self)
        title = QLabel("NEO CONTROL CORE")
        title.setStyleSheet("font-size:18px;font-weight:900;letter-spacing:2px")
        subtitle = QLabel("حافظه و انتخاب‌ها محلی‌اند؛ هیچ دسترسی پنهانی فعال نمی‌شود.")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        form = QFormLayout()
        self.owner = QLineEdit(owner_name)
        self.roaming = QCheckBox("حرکت خودکار کاراکتر")
        self.roaming.setChecked(roaming)
        self.light_theme = QCheckBox("ظاهر روشن")
        self.light_theme.setChecked(light_theme)
        self.web_enabled = QCheckBox("اجازهٔ جست‌وجوی عمومی وب هنگام درخواست")
        self.web_enabled.setChecked(web_enabled)
        form.addRow("نام من", self.owner)
        form.addRow("مدل فعال", QLabel(model))
        form.addRow("محل حافظه", QLabel(data_path))
        form.addRow("رفتار", self.roaming)
        form.addRow("ظاهر", self.light_theme)
        form.addRow("وب", self.web_enabled)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
