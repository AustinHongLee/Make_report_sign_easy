from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHeaderView,
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
        self.add_button = QPushButton("加入目前 values")
        self.import_button = QPushButton("從多個 JSON 匯入")
        self.clear_button = QPushButton("清空")
        self.run_button = QPushButton("執行批次")
        self.run_button.setObjectName("PrimaryButton")

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.add_button)
        header.addWidget(self.import_button)
        header.addWidget(self.clear_button)
        header.addWidget(self.run_button)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(("標籤", "輸出檔", "來源", "Seed", "狀態"))
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.summary = QLabel("尚未加入批次工作")
        self.summary.setObjectName("Muted")

        layout.addLayout(header)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.summary)

        self.add_button.clicked.connect(self.add_current_values_dialog)
        self.import_button.clicked.connect(self.import_json_dialog)
        self.clear_button.clicked.connect(self.view_model.clear)
        self.run_button.clicked.connect(self.view_model.run)
        self.view_model.items_changed.connect(self.set_items)
        self.view_model.batch_finished.connect(self.set_result)
        self.run_button.setEnabled(False)

    def set_busy(self, busy: bool) -> None:
        self.add_button.setEnabled(not busy)
        self.import_button.setEnabled(not busy)
        self.clear_button.setEnabled(not busy)
        self.run_button.setEnabled(not busy and bool(self.view_model.session.batch_items))
        if busy:
            self.summary.setText("批次執行中...")

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

    def import_json_dialog(self) -> None:
        values_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇 values JSON",
            "",
            "JSON files (*.json)",
        )
        if not values_paths:
            return

        output_dir = QFileDialog.getExistingDirectory(self, "選擇批次輸出資料夾")
        if not output_dir:
            return

        for index, values_path in enumerate(values_paths, start=1):
            source = Path(values_path)
            output_path = Path(output_dir) / f"{source.stem}.pdf"
            self.view_model.add_values_path(
                source,
                output_path,
                label=source.stem,
                seed=index,
            )

    def set_items(self, items: tuple) -> None:
        self.table.setRowCount(len(items))
        self.run_button.setEnabled(bool(items))
        for row, item in enumerate(items):
            source = str(item.values_path) if item.values_path else "目前 values"
            values = (
                item.label or f"Job {row + 1}",
                str(item.output_path),
                source,
                "" if item.seed is None else str(item.seed),
                "待執行",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.summary.setText(f"{len(items)} 筆待執行")

    def set_result(self, result) -> None:
        for row, fill_result in enumerate(result.results):
            missing = len(fill_result.missing_fields)
            status = "完成" if missing == 0 else f"完成，缺 {missing}"
            self.table.setItem(row, 4, QTableWidgetItem(status))
        self.summary.setText(f"已產出 {len(result.output_paths)} 份 PDF")
