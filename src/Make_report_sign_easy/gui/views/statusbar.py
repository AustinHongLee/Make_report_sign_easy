from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout

from Make_report_sign_easy.services import TemplateInspection


class ActionStatusBar(QFrame):
    """Bottom validation summary and primary action row."""

    preview_requested = Signal()
    export_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Panel")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        self.summary = QLabel("尚未載入範本")
        self.preview_button = QPushButton("整頁預覽")
        self.preview_button.setEnabled(False)
        self.export_button = QPushButton("匯出 PDF")
        self.export_button.setObjectName("PrimaryButton")
        self.export_button.setEnabled(False)
        layout.addWidget(self.summary)
        layout.addStretch(1)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.export_button)

        self.preview_button.clicked.connect(self.preview_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)

    def set_inspection(self, inspection: TemplateInspection) -> None:
        self.summary.setText(
            f"{len(inspection.matched_keys)} 已填 · "
            f"{len(inspection.missing_value_keys)} 缺值 · "
            f"{len(inspection.extra_value_keys)} 多餘"
        )
        self.preview_button.setEnabled(bool(inspection.matched_keys))
        self.export_button.setEnabled(bool(inspection.matched_keys))
