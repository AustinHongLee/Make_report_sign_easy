from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from Make_report_sign_easy.pdf import load_freetext_template
from Make_report_sign_easy.pdf.models import Template


@dataclass(frozen=True)
class TemplateInspection:
    template: Template
    value_keys: tuple[str, ...]
    matched_keys: tuple[str, ...]
    missing_value_keys: tuple[str, ...]
    extra_value_keys: tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        return not self.missing_value_keys and not self.extra_value_keys


class TemplateService:
    """Use-case service for template field discovery and value checks."""

    def load_template(
        self,
        template_path: str | Path,
        *,
        page_index: int = 0,
    ) -> Template:
        return load_freetext_template(template_path, page_index=page_index)

    def inspect(
        self,
        template_path: str | Path,
        *,
        values: Mapping[str, object] | None = None,
        page_index: int = 0,
    ) -> TemplateInspection:
        template = self.load_template(template_path, page_index=page_index)
        field_keys = set(template.field_keys)
        value_keys = set(values.keys()) if values else set()

        return TemplateInspection(
            template=template,
            value_keys=tuple(sorted(value_keys)),
            matched_keys=tuple(sorted(field_keys & value_keys)),
            missing_value_keys=tuple(sorted(field_keys - value_keys)),
            extra_value_keys=tuple(sorted(value_keys - field_keys)),
        )
