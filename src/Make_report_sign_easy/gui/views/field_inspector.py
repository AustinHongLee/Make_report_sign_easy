from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout


class FieldInspector(QFrame):
    """Right panel for the currently selected field."""

    field_preview_requested = Signal()

    def __init__(self, view_model) -> None:
        super().__init__()
        self.setObjectName("Panel")
        self.setFixedWidth(300)
        self.view_model = view_model
        self._current_key: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("選取欄位")
        title.setObjectName("Muted")
        self.key_label = QLabel("尚未選取")
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("輸入此欄位的值")
        self.profile_check = QCheckBox("此欄覆寫 profile")
        self.preview_button = QPushButton("預覽此欄")
        self.preview_button.setEnabled(False)

        layout.addWidget(title)
        layout.addWidget(self.key_label)
        layout.addWidget(QLabel("值"))
        layout.addWidget(self.value_edit)
        layout.addWidget(self.profile_check)
        layout.addWidget(self.preview_button)
        layout.addStretch(1)

        self.value_edit.editingFinished.connect(self._commit_value)
        self.preview_button.clicked.connect(self.field_preview_requested.emit)
        self.view_model.selected_key_changed.connect(self.set_selected_key)
        self.view_model.values_changed.connect(self._refresh_value)

    def set_selected_key(self, key: str | None) -> None:
        self._current_key = key
        if key is None:
            self.key_label.setText("尚未選取")
            self.value_edit.setText("")
            self.value_edit.setEnabled(False)
            self.preview_button.setEnabled(False)
            return

        self.key_label.setText(key)
        self.value_edit.setEnabled(True)
        self.preview_button.setEnabled(True)
        self._refresh_value(self.view_model.session.values)

    def _refresh_value(self, values: dict) -> None:
        if self._current_key is None:
            return
        value = values.get(self._current_key, "")
        if self.value_edit.text() != str(value):
            self.value_edit.setText(str(value))

    def _commit_value(self) -> None:
        if self._current_key is not None:
            self.view_model.set_value(self._current_key, self.value_edit.text())
