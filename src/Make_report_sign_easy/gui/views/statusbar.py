from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QHBoxLayout

from Make_report_sign_easy.services import TemplateInspection


class ActionStatusBar(QFrame):
    """Bottom validation summary and primary action row."""

    preview_requested = Signal()
    export_requested = Signal()
    batch_requested = Signal()

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
        self.export_button.clicked.connect(self._emit_primary)
        self._batch_mode = False

    def set_inspection(self, inspection: TemplateInspection) -> None:
        if self._batch_mode:
            return
        self.summary.setText(
            f"{len(inspection.matched_keys)} 已填 · "
            f"{len(inspection.missing_value_keys)} 缺值 · "
            f"{len(inspection.extra_value_keys)} 多餘"
        )
        self.preview_button.setEnabled(bool(inspection.matched_keys))
        self.export_button.setEnabled(bool(inspection.matched_keys))

    def set_single_mode(self, inspection: TemplateInspection | None) -> None:
        self._batch_mode = False
        self.preview_button.setVisible(True)
        self.preview_button.setText("整頁預覽")
        self.export_button.setText("匯出 PDF")
        self.export_button.setObjectName("PrimaryButton")
        if inspection is None:
            self.summary.setText("尚未載入範本，請先選範本")
            self.preview_button.setEnabled(False)
            self.export_button.setEnabled(False)
        else:
            self.set_inspection(inspection)

    def set_batch_mode(self, item_count: int) -> None:
        self._batch_mode = True
        self.preview_button.setVisible(False)
        self.export_button.setText("執行批次")
        self.export_button.setEnabled(item_count > 0)
        self.summary.setText(f"批次清單 {item_count} 筆")

    def set_batch_result(self, result) -> None:
        if not self._batch_mode:
            return
        self.export_button.setEnabled(True)
        self.summary.setText(f"已產出 {len(result.output_paths)} 份 PDF")

    def set_busy(self, busy: bool, message: str) -> None:
        self.summary.setText(message)
        self.preview_button.setEnabled(not busy and self.preview_button.isVisible())
        self.export_button.setEnabled(not busy)

    def _emit_primary(self) -> None:
        if self._batch_mode:
            self.batch_requested.emit()
        else:
            self.export_requested.emit()
