from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class BatchWorkbench(QWidget):
    """Batch fill workbench backed by BatchViewModel."""

    def __init__(self, view_model) -> None:
        super().__init__()
        self.view_model = view_model

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("批次工作台")
        add_button = QPushButton("加入目前 values")
        clear_button = QPushButton("清空")
        run_button = QPushButton("執行批次")
        run_button.setObjectName("PrimaryButton")

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(add_button)
        header.addWidget(clear_button)
        header.addWidget(run_button)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(("標籤", "輸出檔", "來源", "狀態"))
        self.table.horizontalHeader().setStretchLastSection(True)
        self.summary = QLabel("尚未加入批次工作")
        self.summary.setObjectName("Muted")

        layout.addLayout(header)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.summary)

        add_button.clicked.connect(self.add_current_values_dialog)
        clear_button.clicked.connect(self.view_model.clear)
        run_button.clicked.connect(self.view_model.run)
        self.view_model.items_changed.connect(self.set_items)
        self.view_model.batch_finished.connect(self.set_result)

    def add_current_values_dialog(self) -> None:
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "新增批次輸出",
            "",
            "PDF files (*.pdf)",
        )
        if output_path:
            label = Path(output_path).stem
            self.view_model.add_current_values(output_path, label=label)

    def set_items(self, items: tuple) -> None:
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            source = str(item.values_path) if item.values_path else "目前 values"
            values = (
                item.label or f"Job {row + 1}",
                str(item.output_path),
                source,
                "待執行",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.summary.setText(f"{len(items)} 筆待執行")

    def set_result(self, result) -> None:
        for row, fill_result in enumerate(result.results):
            missing = len(fill_result.missing_fields)
            status = "完成" if missing == 0 else f"完成，缺 {missing}"
            self.table.setItem(row, 3, QTableWidgetItem(status))
        self.summary.setText(f"已產出 {len(result.output_paths)} 份 PDF")
