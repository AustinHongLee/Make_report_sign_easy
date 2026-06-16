from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from Make_report_sign_easy.core import RenderProfile
from Make_report_sign_easy.pdf.models import Template
from Make_report_sign_easy.pdf.models import FillResult
from Make_report_sign_easy.services import TemplateInspection
from Make_report_sign_easy.services import BatchFillItem, BatchFillResult


@dataclass
class AppSession:
    """Mutable GUI session state shared by view models."""

    template: Template | None = None
    values: dict[str, object] = field(default_factory=dict)
    values_path: Path | None = None
    profile: RenderProfile | None = None
    inspection: TemplateInspection | None = None
    selected_key: str | None = None
    last_output_path: Path | None = None
    preview_pdf_path: Path | None = None
    preview_result: FillResult | None = None
    field_preview_key: str | None = None
    batch_items: list[BatchFillItem] = field(default_factory=list)
    batch_result: BatchFillResult | None = None
    clear_annots: bool = True
    random: bool = False
    seed: int | None = None
