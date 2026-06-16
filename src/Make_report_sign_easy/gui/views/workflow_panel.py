from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from Make_report_sign_easy.gui.theme.tokens import INK_BLUE, MISSING_YELLOW, READY_GREEN
from Make_report_sign_easy.pdf.models import Template
from Make_report_sign_easy.services import TemplateInspection


class WorkflowPanel(QFrame):
    """Left workflow/status rail."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("工作流程")
        title.setObjectName("Muted")
        layout.addWidget(title)

        self.template_label = QLabel("1 範本 - 尚未載入")
        self.fields_label = QLabel("2 欄位 - 0")
        self.values_label = QLabel("3 數值 - 0/0")
        self.preview_label = QLabel("4 預覽 - 待產生")
        self.export_label = QLabel("5 匯出 - 待選擇")
        self.missing_label = QLabel("缺值 0")

        for label in (
            self.template_label,
            self.fields_label,
            self.values_label,
            self.preview_label,
            self.export_label,
            self.missing_label,
        ):
            label.setMinimumHeight(28)
            layout.addWidget(label)

        layout.addStretch(1)

    def set_template(self, template: Template) -> None:
        self.template_label.setText("1 範本 - 已載入")
        self.fields_label.setText(f"2 欄位 - {len(template.fields)}")
        self.template_label.setStyleSheet(f"color: {READY_GREEN}; font-weight: 600;")

    def set_inspection(self, inspection: TemplateInspection) -> None:
        matched = len(inspection.matched_keys)
        total = len(inspection.template.fields)
        missing = len(inspection.missing_value_keys)
        extra = len(inspection.extra_value_keys)
        self.values_label.setText(f"3 數值 - {matched}/{total}")
        self.missing_label.setText(f"缺值 {missing} · 多餘 {extra}")
        color = READY_GREEN if inspection.is_complete else MISSING_YELLOW
        self.values_label.setStyleSheet(f"color: {color}; font-weight: 600;")
        self.preview_label.setStyleSheet(f"color: {INK_BLUE};")

    def set_preview_ready(self) -> None:
        self.preview_label.setText("4 預覽 - 已產生")
        self.preview_label.setStyleSheet(f"color: {READY_GREEN}; font-weight: 600;")

    def set_export_ready(self) -> None:
        self.export_label.setText("5 匯出 - 已完成")
        self.export_label.setStyleSheet(f"color: {READY_GREEN}; font-weight: 600;")

    def set_single_mode(self) -> None:
        self.preview_label.setText("4 預覽 - 待產生")
        self.export_label.setText("5 匯出 - 待選擇")
        self.preview_label.setStyleSheet(f"color: {INK_BLUE};")
        self.export_label.setStyleSheet("")

    def set_batch_mode(self, item_count: int) -> None:
        self.preview_label.setText("4 批次 - 待執行")
        self.export_label.setText(f"5 佇列 - {item_count} 筆")
        self.preview_label.setStyleSheet(f"color: {INK_BLUE};")
        self.export_label.setStyleSheet(f"color: {READY_GREEN if item_count else MISSING_YELLOW}; font-weight: 600;")

    def set_batch_result(self, result) -> None:
        self.preview_label.setText("4 批次 - 已完成")
        self.export_label.setText(f"5 產出 - {len(result.output_paths)} 份")
        self.preview_label.setStyleSheet(f"color: {READY_GREEN}; font-weight: 600;")
        self.export_label.setStyleSheet(f"color: {READY_GREEN}; font-weight: 600;")
