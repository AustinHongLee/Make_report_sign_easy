from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from Make_report_sign_easy.core import RenderProfile
from Make_report_sign_easy.pdf.fill import fill_pdf
from Make_report_sign_easy.pdf.models import FillResult
from Make_report_sign_easy.services.values import ValueSetService


@dataclass(frozen=True)
class FillDocumentRequest:
    template_path: Path
    output_path: Path
    values_path: Path | None = None
    values: Mapping[str, object] | None = None
    clear_annots: bool = False
    random: bool = False
    seed: int | None = None
    profile: RenderProfile | None = None


class FillDocumentService:
    """Use-case service for filling a PDF from a JSON value mapping."""

    def __init__(self, value_sets: ValueSetService | None = None) -> None:
        self.value_sets = value_sets or ValueSetService()

    def run(self, request: FillDocumentRequest) -> FillResult:
        if request.values is None:
            if request.values_path is None:
                raise ValueError("values or values_path is required")
            values = self.value_sets.load_json(request.values_path).values
        else:
            values = request.values

        return fill_pdf(
            template_path=request.template_path,
            values=values,
            output_path=request.output_path,
            clear_annots=request.clear_annots,
            random=request.random,
            seed=request.seed,
            profile=request.profile,
        )
