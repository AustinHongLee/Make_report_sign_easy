from __future__ import annotations

from pathlib import Path
from typing import Mapping

from PySide6.QtCore import QObject, Signal

from Make_report_sign_easy.gui.session import AppSession
from Make_report_sign_easy.services import TemplateService, ValueSetService
from Make_report_sign_easy.services import TemplateInspection


class TemplateViewModel(QObject):
    """View-model for template loading, values, inspection, and selection."""

    template_loaded = Signal(object)
    values_changed = Signal(dict)
    inspection_changed = Signal(object)
    selected_key_changed = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        session: AppSession,
        templates: TemplateService | None = None,
        value_sets: ValueSetService | None = None,
    ) -> None:
        super().__init__()
        self.session = session
        self.templates = templates or TemplateService()
        self.value_sets = value_sets or ValueSetService()

    def load_template(self, path: str | Path, page_index: int = 0) -> None:
        try:
            template = self.templates.load_template(path, page_index=page_index)
        except Exception as exc:
            self.error.emit(str(exc))
            return

        self.session.template = template
        self.session.selected_key = template.field_keys[0] if template.field_keys else None
        self.template_loaded.emit(template)
        self.selected_key_changed.emit(self.session.selected_key)
        self.inspect()

    def load_values(self, path: str | Path) -> None:
        try:
            value_set = self.value_sets.load_json(path)
        except Exception as exc:
            self.error.emit(str(exc))
            return

        self.session.values = dict(value_set.values)
        self.values_changed.emit(dict(self.session.values))
        self.inspect()

    def set_value(self, key: str, value: object) -> None:
        self.session.values[key] = value
        self.values_changed.emit(dict(self.session.values))
        self.inspect()

    def set_values(self, values: Mapping[str, object]) -> None:
        self.session.values = dict(values)
        self.values_changed.emit(dict(self.session.values))
        self.inspect()

    def select_key(self, key: str | None) -> None:
        self.session.selected_key = key
        self.selected_key_changed.emit(key)

    def inspect(self) -> TemplateInspection | None:
        if self.session.template is None:
            return None

        inspection = self.templates.inspect(
            self.session.template.path,
            values=self.session.values,
        )
        self.session.inspection = inspection
        self.inspection_changed.emit(inspection)
        return inspection
