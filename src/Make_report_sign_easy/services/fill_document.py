from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from Make_report_sign_easy.core import RenderProfile
from Make_report_sign_easy.pdf.fill import fill_pdf
from Make_report_sign_easy.pdf.models import FillResult


@dataclass(frozen=True)
class FillDocumentRequest:
    template_path: Path
    values_path: Path
    output_path: Path
    clear_annots: bool = False
    random: bool = False
    seed: int | None = None
    profile: RenderProfile | None = None


class FillDocumentService:
    """Use-case service for filling a PDF from a JSON value mapping."""

    def run(self, request: FillDocumentRequest) -> FillResult:
        if not request.values_path.exists():
            raise FileNotFoundError(request.values_path)

        with request.values_path.open("r", encoding="utf-8") as f:
            values = json.load(f)
        if not isinstance(values, dict):
            raise ValueError("values must be a JSON object mapping {field_key: text}")

        return fill_pdf(
            template_path=request.template_path,
            values=values,
            output_path=request.output_path,
            clear_annots=request.clear_annots,
            random=request.random,
            seed=request.seed,
            profile=request.profile,
        )
